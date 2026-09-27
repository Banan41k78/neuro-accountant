# src/ingest/build_index.py
import argparse
from pathlib import Path

import chromadb
from llama_index.core import (
    VectorStoreIndex, StorageContext, Settings as LISettings,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

from src.config import settings
from src.ingest.loaders import load_directory


def build(
    data_path: str | Path,
    collection_name: str,
    *,
    recreate: bool = True,
) -> None:
    data_path = Path(data_path)
    if not data_path.exists():
        raise FileNotFoundError(f"Папка не найдена: {data_path}")

    LISettings.embed_model = HuggingFaceEmbedding(model_name=settings.embed_model)
    LISettings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=64)

    docs = load_directory(data_path)
    if not docs:
        print(f"  В {data_path} нет поддерживаемых файлов")
        return
    print(f" Загружено документов: {len(docs)}")
    for d in docs:
        print(f"   - {d.metadata.get('file_name', '?')} ({len(d.text)} симв.)")

    client = chromadb.PersistentClient(path=settings.chroma_path)

    if recreate:
        try:
            client.delete_collection(collection_name)
            print(f"  Коллекция '{collection_name}' удалена")
        except Exception:
            pass

    collection = client.get_or_create_collection(collection_name)
    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    VectorStoreIndex.from_documents(
        docs,
        storage_context=storage_context,
        show_progress=True,
    )
    print(f" Коллекция '{collection_name}' сохранена в {settings.chroma_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--collection", required=True)
    parser.add_argument("--append", action="store_true",
                        help="Дописать в существующую коллекцию, не удалять")
    args = parser.parse_args()

    build(args.data, args.collection, recreate=not args.append)


if __name__ == "__main__":
    main()