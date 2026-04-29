"""MCP search tools for Confluence, Jira, and product specs."""

from typing import Literal

from langchain_core.documents import Document

from mcp_search.config import build_app_config
from mcp_search.vector_store import vector_store

config = build_app_config()


async def search_confluence(
    query: str,
    space_key: Literal["PL", "PEX", "DCC"],
    top_k: int = 10,
) -> list[Document]:
    """Run similarity search in a Confluence space and return markdown."""
    collection_name = f"confluence_{space_key.lower()}"
    store = vector_store(collection_name, config)
    documents = await store.asimilarity_search(query, top_k)

    return documents
