# chroma_db

Локальное хранилище векторных индексов ChromaDB.

## Что здесь

- `chroma.sqlite3` — метаданные коллекций
- `<uuid>/` — сегменты с эмбеддингами (по одной папке на коллекцию)

## Коллекции

| Имя | Источник | Назначение |
|---|---|---|
| `common` | `data/common/` | Общие нормы: НК РФ, ПБУ, ФСБУ, инструкции 1С |
| `contour_romashka` | `data/contour/romashka/` | Внутренние документы ООО «Ромашка» |

## Как заполняется

Автоматически:

```powershell
python -m src.ingest.build_index --data ./data/common --collection common
python -m src.ingest.build_index --data ./data/contour/romashka --collection contour_romashka