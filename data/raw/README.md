
---

##  `data/raw/README.md`

```markdown
# data/raw

Кэш скачанных данных до обработки.

## Что здесь появляется

- `gdoc_<id>.txt` — экспортированные Google Docs
- `web_*.html` — сохранённые веб-страницы (если решите кэшировать)
- временные PDF до перемещения в `common/`

## Зачем нужен

Чтобы **не дёргать внешние источники** при каждом переиндексировании. Если Google Doc недоступен или сайт лежит — используем кэш.

## Как заполняется

Автоматически при `fetch_gdocs`:

```powershell
python -m src.ingest.fetch_gdocs --ids 1cVeK50lq4RUWIN9z7wYr...
```

## Очистка
Папка не нужна в git и её можно удалять без последствий:

```powershell
Remove-Item .\data\raw\* -Recurse -Force
```