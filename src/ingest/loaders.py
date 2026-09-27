"""Универсальные загрузчики документов для индексации."""
from __future__ import annotations

import hashlib
from pathlib import Path

import requests
from llama_index.core import Document, SimpleDirectoryReader
from llama_index.readers.web import TrafilaturaWebReader


SUPPORTED_EXTS = [".txt", ".md", ".pdf", ".docx", ".csv", ".html"]


def _sha1(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def load_directory(path: str | Path) -> list[Document]:
    """Рекурсивно читает все поддерживаемые файлы из папки."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Папка не найдена: {path}")

    docs = SimpleDirectoryReader(
        input_dir=str(path),
        recursive=True,
        required_exts=SUPPORTED_EXTS,
        filename_as_id=True,
    ).load_data()
    return docs


def load_web(urls: list[str]) -> list[Document]:
    """Загружает веб-страницы, вытаскивает основной текст."""
    if not urls:
        return []
    try:
        return TrafilaturaWebReader().load_data(urls)
    except Exception as e:
        print(f"  Не удалось загрузить веб-страницы: {e}")
        return []


def load_gdoc(doc_id: str, cache_dir: Path | None = None) -> Document | None:
    """
    Загружает Google Doc по ID через экспорт в txt.
    Если cache_dir задан — кэширует результат на диск.
    """
    url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f" Google Doc {doc_id}: {e}")
        return None

    text = r.text
    if cache_dir is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = cache_dir / f"gdoc_{doc_id}.txt"
        cache_path.write_text(text, encoding="utf-8")

    return Document(
        text=text,
        metadata={
            "source": f"https://docs.google.com/document/d/{doc_id}/",
            "type": "google_docs",
            "doc_id": doc_id,
            "hash": _sha1(text),
        },
    )


def load_text_file(path: str | Path, source_label: str | None = None) -> Document | None:
    """Читает один текстовый файл и возвращает Document."""
    path = Path(path)
    if not path.exists():
        print(f"  Файл не найден: {path}")
        return None
    text = path.read_text(encoding="utf-8")
    return Document(
        text=text,
        metadata={
            "source": source_label or str(path),
            "file_name": path.name,
            "type": "text",
        },
    )