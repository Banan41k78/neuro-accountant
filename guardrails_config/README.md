
---

## `guardrails_config/README.md`

```markdown
# guardrails_config

Правила NeMo Guardrails.

## Что здесь

- `config.yml` — модель, инструкции, flow-правила (пока не создан)
- `prompts.yml` — тексты промптов (опционально)
- `patterns.co` — Colang-скрипты (для сложных сценариев)

## Как работает

Двухуровневая защита:

1. **`src/guardrails/fast_filter.py`** — regex, мгновенно, ловит ~90%.
2. **NeMo Guardrails** (эта папка) — LLM-проверка, ловит замаскированные обходы.

## Минимальный `config.yml`

```yaml
models:
  - type: main
    engine: openai
    model: gpt-4.1-nano

instructions:
  - type: general
    content: |
      Ты — бухгалтерский ассистент. Отказывайся отвечать на запросы про
      обнал, уход от налогов, подделку документов, персональные данные.

rails:
  input:
    flows:
      - self check input
  output:
    flows:
      - self check output