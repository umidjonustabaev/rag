"""Confluence page loader with optional Dockling-based markdown parsing."""

from datetime import datetime

from atlassian.bitbucket import cloud
from langchain_community.document_loaders.confluence import (
    ConfluenceLoader as BaseConfluenceLoader,
)
from langchain_core.documents import Document
from pydantic import Field, model_validator
from pydantic.dataclasses import dataclass

from ingester.content_parser import parse_to_markdown


def _write_html_header(body: str) -> str:
    """Write the HTML header to the beginning of the body."""
    return f'<html><head><meta charset="utf-8"></head><body>{body}</body></html>'


@dataclass
class ConfluencePageView:
    """Rendered view of a Confluence page body."""

    value: str | None


@dataclass
class ConfluencePageBody:
    """Container for the rendered body of a Confluence page."""

    view: ConfluencePageView | None = None


@dataclass
class ConfluenceLinks:
    """Navigation links associated with a Confluence page."""

    webui: str


@dataclass
class ConfluencePageVersion:
    """Version info for a Confluence page, stored as a Unix timestamp."""

    number: int | str = Field(alias="when")

    @model_validator(mode="after")
    def convert_unix_timestamp(self) -> "ConfluencePageVersion":
        """Convert the ISO-8601 ``when`` value to a Unix timestamp."""
        self.number = int(datetime.fromisoformat(self.number).timestamp())
        return self


@dataclass
class ConfluencePage:
    """Structured representation of a Confluence page with computed metadata."""

    id: str
    title: str
    base_url: str
    body: ConfluencePageBody
    links: ConfluenceLinks = Field(alias="_links")
    version: ConfluencePageVersion | None = None
    metadata: dict | None = None

    def __str__(self) -> str:
        """Return the raw HTML view of the page body."""
        return _write_html_header(self.body.view.value)

    @model_validator(mode="after")
    def overwrite_metadata(self) -> "ConfluencePage":
        """Populate ``metadata`` from the page's title, id, URL, and version."""
        self.metadata = {
            "title": self.title,
            "id": self.id,
            "source": self.base_url.strip("/") + self.links.webui,
            "version": self.version.number if self.version else None,
        }
        return self


class ConfluenceLoader(BaseConfluenceLoader):
    """Confluence loader that optionally converts pages to Markdown via Dockling."""

    def __init__(self, parse_with_dockling: bool = False, *args, **kwargs) -> None:
        """Initialize the loader with an option to parse pages with Dockling."""
        super().__init__(cloud=True, *args, **kwargs)
        self.parse_with_dockling = parse_with_dockling

    def process_page(self, page: dict, *args, **kwargs) -> Document:
        """Process a raw Confluence page dict into a LangChain ``Document``."""
        if not self.parse_with_dockling:
            return super().process_page(page, *args, **kwargs)

        confluence_page = ConfluencePage(base_url=self.base_url, **page)
        md_content = parse_to_markdown(str(confluence_page))

        return Document(
            page_content=md_content,
            metadata=confluence_page.metadata,
        )
