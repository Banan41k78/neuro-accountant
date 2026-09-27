"""Полный цикл: fetch common → build common → build contour."""
from __future__ import annotations

from pathlib import Path

from src.ingest.fetch_common import fetch_all
from src.ingest.build_index import build


COMMON_DATA = Path("./data/common")
CONTOUR_DATA = Path("./data/contour/romashka")


def main() -> None:
    print("=" * 70)
    print("ШАГ 1/3: Загрузка общих документов")
    print("=" * 70)
    fetch_all()

    print()
    print("=" * 70)
    print("ШАГ 2/3: Индексация общей базы")
    print("=" * 70)
    build(COMMON_DATA, "common", recreate=True)

    print()
    print("=" * 70)
    print("ШАГ 3/3: Индексация контурной базы")
    print("=" * 70)
    if not CONTOUR_DATA.exists() or not any(CONTOUR_DATA.rglob("*.*")):
        print(f"  Папка {CONTOUR_DATA} пуста — пропускаю.")
        print("   Положите туда txt/pdf с документами ООО «Ромашка».")
    else:
        build(CONTOUR_DATA, "contour_romashka", recreate=True)

    print()
    print(" Готово. Проверка:")
    print("   python -c \"import chromadb; "
          "c=chromadb.PersistentClient('./chroma_db'); "
          "print([x.name for x in c.list_collections()])\"")


if __name__ == "__main__":
    main()