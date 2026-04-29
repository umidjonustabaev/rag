from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from ingester.config import Config


def _embeddings(model: str, api_key: str) -> GoogleGenerativeAIEmbeddings:
    """Build the default Gemini embedding model from app config."""
    return GoogleGenerativeAIEmbeddings(model=model, api_key=api_key)


def _init_qdrant_client(host: str, port: int) -> QdrantClient:
    return QdrantClient(
        host=host,
        port=port,
    )


def vector_store(collection_name: str, app_config: Config) -> QdrantVectorStore:
    client = _init_qdrant_client(app_config.qdrant.host, app_config.qdrant.port)
    embeddings = _embeddings(app_config.embedding.model, app_config.embedding.api_key)
    return QdrantVectorStore(client=client, collection_name=collection_name, embedding=embeddings)
