"""Загрузка общих (публичных) документов в data/common/."""
from __future__ import annotations

from pathlib import Path

import requests

from src.ingest.loaders import load_web, load_gdoc


COMMON_DIR = Path("./data/common")
RAW_DIR = Path("./data/raw")

# Публичные PDF/веб-источники
PDF_SOURCES = [
    {
        "url": "https://elar.urfu.ru/bitstream/10995/42396/1/978-5-7996-1820-9_2016.pdf",
        "filename": "accounting_guide.pdf",
    },
]

WEB_SOURCES = [
    "https://1cfresh.com/",
]

# Google Docs, которые дописываем в общую базу
GDOC_IDS = [
    "1cVeK50lq4RUWIN9z7wYr_DKTKceul9V2aJ_bZKjKxCo",
]


def download_pdfs() -> int:
    COMMON_DIR.mkdir(parents=True, exist_ok=True)
    saved = 0
    for src in PDF_SOURCES:
        out = COMMON_DIR / src["filename"]
        if out.exists():
            print(f"⏭  Уже есть: {out.name}")
            continue
        try:
            r = requests.get(src["url"], timeout=60)
            r.raise_for_status()
            out.write_bytes(r.content)
            print(f" {out.name} ({len(r.content) // 1024} КБ)")
            saved += 1
        except Exception as e:
            print(f" {src['url']}: {e}")
    return saved


def download_web() -> int:
    """Сохраняем веб-страницы как .txt, чтобы они попали в общий индекс."""
    COMMON_DIR.mkdir(parents=True, exist_ok=True)
    docs = load_web(WEB_SOURCES)
    for i, doc in enumerate(docs):
        out = COMMON_DIR / f"web_{i:02d}.txt"
        out.write_text(doc.text, encoding="utf-8")
        print(f" {out.name} ({len(doc.text)} симв.)")
    return len(docs)


def download_gdocs() -> int:
    """Google Docs сохраняем как txt прямо в data/common/."""
    COMMON_DIR.mkdir(parents=True, exist_ok=True)
    saved = 0
    for doc_id in GDOC_IDS:
        doc = load_gdoc(doc_id, cache_dir=RAW_DIR)
        if doc is None:
            continue
        out = COMMON_DIR / f"gdoc_{doc_id[:8]}.txt"
        out.write_text(doc.text, encoding="utf-8")
        print(f" {out.name} ({len(doc.text)} симв.)")
        saved += 1
    return saved


def fetch_all() -> None:
    print("=== Загрузка общей базы ===")
    n_pdf = download_pdfs()
    n_web = download_web()
    n_doc = download_gdocs()
    print(f"\nИтого: PDF={n_pdf}, web={n_web}, gdoc={n_doc}")


if __name__ == "__main__":
    fetch_all()