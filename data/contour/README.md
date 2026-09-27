
---

##  `data/contour/README.md`

# data/contour

Контурные базы знаний. Приватные документы организаций.

## Принцип мультитенантности

**Одна подпапка — одна организация.** Не смешивайте документы разных клиентов.

```
contour/
├── romashka/ ← ООО «Ромашка»
├── tulip/ ← ООО «Тюльпан»
└── ip_petrov/ ← ИП Петров
```

Каждой организации соответствует **отдельная коллекция** в ChromaDB:
- `romashka` → `contour_romashka`
- `tulip` → `contour_tulip`
- `ip_petrov` → `contour_ip_petrov`

## Структура одной организации
```
romashka/
├── accounting_policy.txt ← учётная политика
├── chart_of_accounts.txt ← рабочий план счетов
├── contracts/ ← договоры
├── invoices/ ← счета-фактуры
├── osv/ ← оборотно-сальдовые ведомости
├── employees/ ← штатное расписание, приказы
└── deadlines.txt ← календарь бухгалтера
```


## Индексация

```powershell
python -m src.ingest.build_index --data ./data/contour/romashka --collection contour_romashka