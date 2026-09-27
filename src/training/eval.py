"""
Оценка модели (LoRA или базовой) на наборе эталонных QA.

Формат data/eval.jsonl:
    {"question": "...", "expected": "...", "keywords": ["ндс", "20"]}

Запуск:
    python -m src.training.eval --eval-file data/eval.jsonl
    python -m src.training.eval --eval-file data/eval.jsonl --no-lora
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.config import settings


def _load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _build_prompt(question: str) -> str:
    return (
        "Ты — нейро-бухгалтер. Отвечай точно, ссылайся на нормы НК РФ и ФСБУ.\n\n"
        f"Вопрос: {question}\n"
        "Ответ:"
    )


def _check_keywords(answer: str, keywords: list[str]) -> tuple[int, int]:
    if not keywords:
        return 0, 0
    answer_low = answer.lower()
    hits = sum(1 for k in keywords if k.lower() in answer_low)
    return hits, len(keywords)


def main() -> int:
    parser = argparse.ArgumentParser(prog="src.training.eval")
    parser.add_argument("--eval-file", default="./data/eval.jsonl")
    parser.add_argument("--adapter", default=settings.adapter_path)
    parser.add_argument("--no-lora", action="store_true",
                        help="Не подключать LoRA-адаптер")
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    eval_file = Path(args.eval_file)
    if not eval_file.exists():
        print(f"[!] Файл не найден: {eval_file}")
        print("-   Создайте data/eval.jsonl с примерами вида:")
        print('-   {"question": "...", "expected": "...", "keywords": ["ндс","20"]}')
        return 1

    # --- Загрузка модели ----------------------------------------------------
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    use_lora = not args.no_lora and Path(args.adapter).exists()

    print(f"- Базовая модель: {settings.base_model}")
    print(f"- LoRA: {'да, ' + args.adapter if use_lora else 'нет (только базовая)'}")

    tokenizer = AutoTokenizer.from_pretrained(
        settings.base_model, token=settings.hf_token or None,
    )
    tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        settings.base_model,
        device_map="auto" if torch.cuda.is_available() else None,
        token=settings.hf_token or None,
    )

    if use_lora:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, args.adapter)

    model.eval()
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # --- Прогон -------------------------------------------------------------
    rows = _load_jsonl(eval_file)
    if args.limit:
        rows = rows[: args.limit]

    print(f"\n Примеров: {len(rows)}\n")

    total_kw_hits = 0
    total_kw = 0

    for i, row in enumerate(rows, 1):
        q = row["question"]
        expected = row.get("expected", "")
        keywords = row.get("keywords", [])

        prompt = _build_prompt(q)
        inputs = tokenizer(prompt, return_tensors="pt").to(device)

        with torch.no_grad():
            out = model.generate(
                **inputs,
                max_new_tokens=args.max_new_tokens,
                temperature=0.1,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
            )

        answer = tokenizer.decode(
            out[0][inputs["input_ids"].shape[1]:],
            skip_special_tokens=True,
        ).strip()

        hits, total = _check_keywords(answer, keywords)
        total_kw_hits += hits
        total_kw += total

        print(f"[{i}/{len(rows)}] Q: {q}")
        print(f"-   Ожидалось: {expected[:120]}")
        print(f"-   Ответ:    {answer[:200]}")
        if total:
            print(f"[]  Ключевые слова: {hits}/{total}")
        print("-" * 70)

    if total_kw:
        print(f"\n  Итог по ключевым словам: {total_kw_hits}/{total_kw} "
              f"({100 * total_kw_hits / total_kw:.1f}%)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())