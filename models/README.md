
---

## `models/README.md`

```markdown
# models

Артефакты локальных моделей.

## Что здесь

- `lora-adapter/` — LoRA-адаптер, обученный на `data/train.jsonl`
  - `adapter_config.json`
  - `adapter_model.safetensors`
  - `tokenizer.json`, `tokenizer_config.json`

## Как появляется

```powershell
python -m src.training.train_lora `
    --train-file data/train.jsonl `
    --output-dir models/lora-adapter `
    --max-steps 200
```

## Как используется

В src/rag/engines.py — модель подгружает адаптер поверх базовой:
```python
from peft import PeftModel
model = PeftModel.from_pretrained(base_model, "./models/lora-adapter")
```
