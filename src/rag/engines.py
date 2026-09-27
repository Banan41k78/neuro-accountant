import chromadb
from llama_index.core import VectorStoreIndex, Settings as LISettings
from llama_index.core.query_engine import RouterQueryEngine
from llama_index.core.selectors import LLMSingleSelector
from llama_index.core.tools import QueryEngineTool
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai_like import OpenAILike
from llama_index.vector_stores.chroma import ChromaVectorStore

from src.config import settings


def _get_engine(collection_name: str):
    client = chromadb.PersistentClient(path=settings.chroma_path)
    collection = client.get_or_create_collection(collection_name)
    vector_store = ChromaVectorStore(chroma_collection=collection)
    index = VectorStoreIndex.from_vector_store(vector_store)
    return index.as_query_engine(similarity_top_k=5)


def build_router() -> RouterQueryEngine:
    LISettings.embed_model = HuggingFaceEmbedding(model_name=settings.embed_model)
    LISettings.llm = OpenAILike(
        model=settings.openai_model,
        api_base=settings.openai_base_url,
        api_key=settings.openai_api_key,
        is_chat_model=True,
        temperature=0.1,
    )

    common = _get_engine(settings.common_collection)
    contour = _get_engine(settings.contour_collection)

    tools = [
        QueryEngineTool.from_defaults(
            query_engine=common,
            description=(
                "Общие нормы: НК РФ, ПБУ, ФСБУ, ставки налогов, "
                "сроки отчётности, инструкции 1С, письма Минфина."
            ),
        ),
        QueryEngineTool.from_defaults(
            query_engine=contour,
            description=(
                "Документы ООО «Ромашка»: договоры, счета-фактуры, ОСВ, "
                "учётная политика, штатка, контрагенты, суммы по сделкам."
            ),
        ),
    ]

    return RouterQueryEngine(
        selector=LLMSingleSelector.from_defaults(),
        query_engine_tools=tools,
    )