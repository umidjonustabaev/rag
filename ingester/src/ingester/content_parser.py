"""HTML parsing utilities for converting selected page content to Markdown.

his module provides HTMLParser, a small helper around BeautifulSoup and
DocumentConverter to extract the main content from an HTML document.
"""

import logging
import tempfile
from pathlib import Path

from docling.document_converter import DocumentConverter


class HtmlParser:
    """HTML-to-Markdown parser using `DocumentConverter`.

    This parser writes the HTML content to a temporary `.html` file and delegates
    conversion to `DocumentConverter`. The temporary file is removed after use.
    """

    def __init__(self, content: str) -> None:
        """Initialize the parser."""
        self.logger = logging.getLogger(__name__)
        self.content: str = content
        self.converter: DocumentConverter = DocumentConverter()

    def to_markdown(self) -> str:
        """Convert the parser's HTML content to a Markdown string."""
        tmp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".html", encoding="utf-8"
            ) as tmp:
                tmp.write(str(self.content))
                tmp_path = Path(tmp.name)

            conversion_result = self.converter.convert(str(tmp_path))
            docling_document = conversion_result.document
            return docling_document.export_to_markdown()
        finally:
            if tmp_path and tmp_path.exists():
                tmp_path.unlink()


def parse_to_markdown(
    content: str,
) -> str:
    """Parse raw content into structured Markdown based on the source type.

    Factory method that selects the appropriate parsing strategy (HTML or OpenAPI)
    to transform raw strings into clean, chunk-ready Markdown.
    """
    parser = HtmlParser(content)
    return parser.to_markdown()
