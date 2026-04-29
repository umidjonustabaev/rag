"""MCP search tools for Confluence, Jira, and product specs."""

from typing import Literal

from langchain_core.documents import Document

from mcp_search.config import build_app_config
from mcp_search.vector_store import vector_store

config = build_app_config()


async def search_confluence(
    query: str,
    top_k: int = 10,
) -> str:
    """Run similarity search in a Confluence space and return markdown."""
    collection_name = "confluence_pl"
    store = vector_store(collection_name, config)
    documents = await store.asimilarity_search(query, top_k)

    return "\n\n".join(
        [document.page_content for document in documents]
    )
