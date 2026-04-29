"""Confluence crawler module.

This module contains a standalone Confluence crawler implementation with
loading, preprocessing, chunking, batching, and repository upserts.
"""

import logging
import re
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from langchain_community.document_loaders.confluence import ContentFormat
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from pydantic import BaseModel, model_validator
from tqdm import tqdm

from ingester.config import Config
from ingester.confluence_loader import ConfluenceLoader
from ingester.splitter import RecursiveMarkdownHeaderTextSplitter

MIN_TOKENS_PER_CHUNK = 3
MAX_BATCH_SIZE = 100
RE_NEWLINES = re.compile(r"\n+")
RE_LANG_CODE = re.compile(r"^[a-zA-Z]{2}(?:-[a-zA-Z]{2,})?$", re.IGNORECASE)
CHUNKING_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


class ConfluenceSpaceCrawlerOptions(BaseModel):
    """Configuration model for ConfluenceSpaceCrawler."""

    url: str
    token: str
    space_key: str | None = None
    cql: str | None = None
    keep_markdown_format: bool = False
    include_attachments: bool = False
    max_pages: int = 100_000
    include_restricted_content: bool = False
    parse_with_dockling: bool = True

    @model_validator(mode="before")
    @classmethod
    def validate_space_key_cql(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Require at least one of `space_key` or `cql` to be provided.

        Raises:
            ValueError: If both `space_key` and `cql` are missing.

        """
        if not (data.get("space_key") or data.get("cql")):
            raise ValueError("Either space_key or cql must be provided.")

        return data

    @model_validator(mode="after")
    def set_confluence_overrides(self):
        """If both `space_key` and `cql` are provided, prefer `cql` by clearing `space_key`."""
        if self.space_key and self.cql:
            self.space_key = None

        return self


def _options_factory(**kwargs: Any) -> ConfluenceSpaceCrawlerOptions:
    """Create validated crawling options."""
    return ConfluenceSpaceCrawlerOptions(**kwargs)


class ConfluenceSpaceCrawler:
    """Standalone Confluence crawler with inlined core crawling logic."""

    def __init__(
        self,
        app_config: Config,
        vector_store: QdrantVectorStore,
        crawling_options: dict[str, Any] | None = None,
        progress_bar: tqdm | None = None,
    ) -> None:
        self.app_config = app_config
        self.crawling_options = crawling_options or {}
        self.logger = logging.getLogger(__name__)
        self.store = vector_store
        self.options = _options_factory(**self.crawling_options)
        self.version = int(datetime.now(tz=ZoneInfo("UTC")).timestamp())
        self.text_splitter = self._set_text_splitter()
        self.loader = self._init_loader()
        self.progress_bar = progress_bar

    def _preprocess_document(self, document: Document) -> Document:
        """Normalize content, anonymize PII, and clean source metadata."""
        document.page_content = RE_NEWLINES.sub("\n", document.page_content)
        document.metadata["version"] = self.version
        preprocessed_document = document
        source = preprocessed_document.metadata.get("source")
        if isinstance(source, str):
            preprocessed_document.metadata["source"] = source.replace("rest.", "")

        return preprocessed_document

    def _preprocess_chunks(self, document_chunks: list[Document]) -> list[Document]:
        """Filter, annotate, and enrich chunk content with Confluence headers."""
        preprocessed_chunks = []
        chunk_index = 1
        for chunk in document_chunks:
            if self._is_valid_chunk(chunk.page_content):
                chunk.metadata["chunk_id"] = chunk_index
                preprocessed_chunks.append(chunk)
                chunk_index += 1

        return [
            self._add_meta_headers(preprocessed_chunk) for preprocessed_chunk in preprocessed_chunks
        ]

    def _is_valid_chunk(self, text: str) -> bool:
        """Check whether a chunk is meaningful for storage."""
        clean_text = text.strip()
        if not clean_text:
            return False

        if RE_LANG_CODE.match(clean_text):
            self.logger.debug(f"Chunk '{clean_text}' ignored as language code/noise")
            return False

        return len(clean_text.split()) >= MIN_TOKENS_PER_CHUNK

    @contextmanager
    def _with_error_handling(self) -> Generator[None]:
        """Handle anonymization and generic processing exceptions."""
        try:
            yield
        except Exception as ex:
            self.logger.error(f"Failed to process document(s) error: {ex}")

    def crawl(self) -> None:
        """Load, preprocess, chunk, and upsert Confluence documents."""
        batch_container: list[Document] = []

        for document in self.loader.lazy_load():
            if self.progress_bar:
                self.progress_bar.update(1)

            if not document.page_content.strip():
                continue

            with self._with_error_handling():
                processed_doc = self._preprocess_document(document)
                chunks = self.text_splitter.split_documents([processed_doc])
                valid_chunks = self._preprocess_chunks(chunks)
                batch_container.extend(valid_chunks)
                if len(batch_container) >= MAX_BATCH_SIZE:
                    self._flush_batched(batch_container)

        self._flush_batched(batch_container)

    def _flush_batched(self, batch_container: list[Document]) -> None:
        """Upsert any pending documents and clear the batch."""
        if batch_container:
            self.store.add_documents(batch_container)
            batch_container.clear()

    def _add_meta_headers(self, document_chunk: Document) -> Document:
        """Add meta-headers to the chunks."""
        space_name = self.options.space_key or self.crawling_options.get("space_key") or "unknown"
        meta_header = f"# {space_name} > {document_chunk.metadata.get('title', '')}\n\n"
        document_chunk.page_content = meta_header + document_chunk.page_content
        return document_chunk

    def _init_loader(self) -> ConfluenceLoader:
        """Initialize the Confluence loader with crawler options."""
        return ConfluenceLoader(content_format=ContentFormat.VIEW, **self.options.model_dump())

    def _set_text_splitter(self) -> RecursiveMarkdownHeaderTextSplitter:
        """Initialize text splitter"""
        return RecursiveMarkdownHeaderTextSplitter(
            chunk_size=self.app_config.embedding.chunk_size,
            chunk_overlap=self.app_config.embedding.chunk_overlap,
            strip_headers=False,
        )
