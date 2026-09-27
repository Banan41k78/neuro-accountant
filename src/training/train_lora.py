"""
LoRA-дообучение локальной LLM на data/train.jsonl.

Режимы:
    python -m src.training.train_lora --dry-run
    python -m src.training.train_lora --train-file data/train.jsonl --output-dir models/lora-adapter
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.config import settings


# ============================================================================
#  ДАННЫЕ
# ============================================================================

def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Файл не найден: {path}")

    rows: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"[!]  Строка {i}: битый JSON — {e}")
    return rows


def _to_text(example: dict, tokenizer) -> str:
    """
    Приводит пример к строке. Поддерживает два формата:
      A) {"messages": [{role, content}, ...]}  — chat-style
      B) {"instruction", "input", "output"}    — alpaca-style
    """
    if "messages" in example:
        return tokenizer.apply_chat_template(
            example["messages"], tokenize=False, add_generation_prompt=False,
        )

    if "instruction" in example:
        parts = [f"### Инструкция:\n{example['instruction']}"]
        if example.get("input"):
            parts.append(f"### Вход:\n{example['input']}")
        parts.append(f"### Ответ:\n{example.get('output', '')}")
        return "\n\n".join(parts)

    raise ValueError(f"Неизвестный формат примера: {list(example.keys())}")


def dry_run(train_file: Path) -> int:
    """Проверка данных без обучения."""
    rows = _load_jsonl(train_file)
    print(f"- Всего примеров: {len(rows)}")

    if not rows:
        print("[!] Файл пуст.")
        return 1

    formats = {"messages": 0, "alpaca": 0, "unknown": 0}
    lengths: list[int] = []
    for r in rows:
        if "messages" in r:
            formats["messages"] += 1
        elif "instruction" in r:
            formats["alpaca"] += 1
        else:
            formats["unknown"] += 1
        # Грубая оценка длины — по всем строковым значениям
        total = sum(len(str(v)) for v in r.values())
        lengths.append(total)

    print(f"Форматы: {formats}")
    print(f"Длина (символов): min={min(lengths)}, max={max(lengths)}, avg={sum(lengths)//len(lengths)}")

    print("\nПервые 3 примера:")
    for r in rows[:3]:
        print("---")
        print(json.dumps(r, ensure_ascii=False, indent=2)[:400])

    if formats["unknown"]:
        print(f"\n[!]  {formats['unknown']} примеров в неизвестном формате — они будут пропущены.")

    print("\n Данные в порядке." if formats["unknown"] == 0 else "\n[!]  Есть проблемы.")
    return 0


# ============================================================================
#  ОБУЧЕНИЕ
# ============================================================================

def train(
    train_file: Path,
    output_dir: Path,
    *,
    max_steps: int = 200,
    batch_size: int = 2,
    grad_accum: int = 4,
    lr: float = 2e-4,
    lora_r: int = 16,
    lora_alpha: int = 32,
    max_seq_length: int = 1024,
) -> int:
    # Импорты внутри функции — чтобы `--dry-run` работал без torch/peft
    import torch
    from datasets import load_dataset
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        TrainingArguments,
    )
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from trl import SFTTrainer

    if not settings.hf_token:
        print("[!]  HUGGINGFACE_TOKEN не задан в .env")

    print(f"- Базовая модель: {settings.base_model}")
    print(f"- Данные: {train_file}")
    print(f"- Адаптер: {output_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    # --- Токенизатор --------------------------------------------------------
    tokenizer = AutoTokenizer.from_pretrained(
        settings.base_model, token=settings.hf_token or None,
    )
    tokenizer.pad_token = tokenizer.eos_token

    # --- Модель с 4-битной квантизацией ------------------------------------
    use_cuda = torch.cuda.is_available()
    print(f"🖥  Устройство: {'CUDA' if use_cuda else 'CPU'}")

    quant_config = None
    if use_cuda:
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )

    model = AutoModelForCausalLM.from_pretrained(
        settings.base_model,
        quantization_config=quant_config,
        device_map="auto" if use_cuda else None,
        torch_dtype=torch.float32 if not use_cuda else None,
        token=settings.hf_token or None,
    )

    if use_cuda:
        model = prepare_model_for_kbit_training(model)

    lora_config = LoraConfig(
        r=lora_r,
        lora_alpha=lora_alpha,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # --- Датасет ------------------------------------------------------------
    dataset = load_dataset("json", data_files=str(train_file), split="train")

    def formatting_func(example):
        return _to_text(example, tokenizer)

    # --- Тренер -------------------------------------------------------------
    args = TrainingArguments(
        output_dir=str(output_dir),
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=grad_accum,
        warmup_steps=10,
        max_steps=max_steps,
        learning_rate=lr,
        fp16=use_cuda,
        logging_steps=10,
        save_steps=50,
        save_total_limit=2,
        optim="paged_adamw_8bit" if use_cuda else "adamw_torch",
        report_to="none",
        remove_unused_columns=False,
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        formatting_func=formatting_func,
        max_seq_length=max_seq_length,
        args=args,
        peft_config=lora_config,
    )

    print("\n Старт обучения...")
    trainer.train()

    print(f"\n Сохраняю адаптер в {output_dir}")
    trainer.model.save_pretrained(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))
    print(" Готово.")
    return 0


# ============================================================================
#  CLI
# ============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(prog="src.training.train_lora")
    parser.add_argument("--train-file", default="./data/train.jsonl")
    parser.add_argument("--output-dir", default=settings.adapter_path)
    parser.add_argument("--dry-run", action="store_true",
                        help="Только проверить данные, не обучать")
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--grad-accum", type=int, default=4)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--lora-r", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=32)
    parser.add_argument("--max-seq-length", type=int, default=1024)
    args = parser.parse_args()

    train_file = Path(args.train_file)

    if args.dry_run:
        return dry_run(train_file)

    return train(
        train_file,
        Path(args.output_dir),
        max_steps=args.max_steps,
        batch_size=args.batch_size,
        grad_accum=args.grad_accum,
        lr=args.lr,
        lora_r=args.lora_r,
        lora_alpha=args.lora_alpha,
        max_seq_length=args.max_seq_length,
    )


if __name__ == "__main__":
    raise SystemExit(main())