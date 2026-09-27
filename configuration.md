# Конфигурация

## Быстрая справка

Все настройки — в `.env`. Полный список см. `.env.example`.

## LLM

### Через OpenAI-совместимый API

```env
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://api.aitunnel.ru/v1/
OPENAI_MODEL=gpt-4.1-nano
```

### Локально через HuggingFace

```env
BASE_MODEL=Qwen/Qwen2.5-7B-Instruct
ADAPTER_PATH=./models/lora-adapter
```

Затем в `src/rag/engines.py` заменить `OpenAILike` на `HuggingFaceLLM`.

## Эмбеддинги

```env
EMBED_MODEL=intfloat/multilingual-e5-large
```

[!] Смена эмбеддингов требует **полной переиндексации**:

```bash
rm -rf chroma_db
python -m src.ingest.build_index --data ./data/common --collection common
```

## Базы знаний

### Добавить общий документ

```bash
cp my_doc.pdf data/common/
python -m src.ingest.build_index --data ./data/common --collection common
```

### Добавить контурный документ

```bash
cp contract.pdf data/contour/romashka/contracts/
python -m src.ingest.build_index --data ./data/contour/romashka --collection contour_romashka
```

### Не пересоздавать, а дописать

```bash
python -m src.ingest.build_index --data ./data/common --collection common --append
```

## Guardrails

### Regex-правила

Редактировать `src/guardrails/fast_filter.py`, списки `_INPUT_PATTERNS` и `_OUTPUT_PATTERNS`.

### NeMo-правила

Редактировать `guardrails_config/config.yml`. Синтаксис — см. официальную документацию NeMo под вашу версию.

## Мультитенантность

Чтобы добавить организацию:

1. Создать папку: `data/contour/<org>/`
2. Положить документы
3. Построить индекс: `build_index --data ./data/contour/<org> --collection contour_<org>`
4. В `src/rag/engines.py` добавить tool для новой коллекции
5. В запросе передавать `org_id` — роутер выберет нужную базу
