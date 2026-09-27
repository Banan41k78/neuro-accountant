"""Загрузка Google Docs по списку ID из .env или аргументов CLI."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from src.ingest.loaders import load_gdoc


OUT_DIR = Path("./data/common")
RAW_DIR = Path("./data/raw")


def _ids_from_env() -> list[str]:
    raw = os.getenv("GDOC_IDS", "")
    return [x.strip() for x in raw.split(",") if x.strip()]


def fetch(doc_ids: list[str], out_dir: Path, raw_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    saved = 0
    for doc_id in doc_ids:
        doc = load_gdoc(doc_id, cache_dir=raw_dir)
        if doc is None:
            continue
        out = out_dir / f"gdoc_{doc_id[:8]}.txt"
        out.write_text(doc.text, encoding="utf-8")
        print(f" {doc_id} → {out.name} ({len(doc.text)} симв.)")
        saved += 1
    return saved


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ids", nargs="*", default=None,
                        help="ID Google Docs. Если пусто — берём GDOC_IDS из .env")
    parser.add_argument("--out", default=str(OUT_DIR))
    parser.add_argument("--raw", default=str(RAW_DIR))
    args = parser.parse_args()

    ids = args.ids if args.ids else _ids_from_env()
    if not ids:
        print("  Не переданы ID и GDOC_IDS пуст в .env")
        return

    n = fetch(ids, Path(args.out), Path(args.raw))
    print(f"\nЗагружено: {n}")


if __name__ == "__main__":
    main()