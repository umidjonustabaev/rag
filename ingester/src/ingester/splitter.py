from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

DEFAULT_MD_HEADERS_TO_SPLIT = [("#", "Header 1"), ("##", "Header 2")]


def document(content: str, metadata: dict) -> Document:
    """Return instance of Document."""
    return Document(page_content=content, metadata=metadata)


class RecursiveMarkdownHeaderTextSplitter(MarkdownHeaderTextSplitter):
    """Splits Markdown text based on headers."""

    def __init__(
        self,
        chunk_size: int,
        chunk_overlap: int,
        separators: list[str] | None = None,
        headers_to_split_on: list[tuple] | None = None,
        *args,
        **kwargs,
    ):
        """Initialize RecursiveMarkdownHeaderTextSplitter."""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.headers_to_split_on = headers_to_split_on or DEFAULT_MD_HEADERS_TO_SPLIT
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            separators=separators,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        super().__init__(headers_to_split_on=self.headers_to_split_on, *args, **kwargs)

    def _split_document(self, source: Document) -> list[Document]:
        """Split document into chunks."""
        content = source.page_content
        metadata = source.metadata
        document_chunks_header_based = self.split_text(content)
        chunks = self.recursive_splitter.split_documents(document_chunks_header_based)

        return [document(chunk.page_content, (metadata | chunk.metadata)) for chunk in chunks]

    def split_documents(self, sources: list[Document]) -> list[Document]:
        """Split documents into chunks based on headers."""
        result: list[Document] = []
        for source in sources:
            chunks = self._split_document(source)
            result.extend(chunks)

        return result
