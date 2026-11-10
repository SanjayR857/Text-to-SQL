"""
Abstract document parser port.

Defines the contract for parsing unstructured files (PDF, DOCX, XLSX, HTML, images)
into clean, structured text and layout metadata.
"""
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field


class ParsedTable(BaseModel):
    """Extracted table representation from document."""

    model_config = ConfigDict(frozen=True)

    headers: list[str] = Field(default_factory=list)
    rows: list[list[str]] = Field(default_factory=list)
    page_number: int | None = None


class ParsedDocument(BaseModel):
    """Normalized document representation after extraction."""

    model_config = ConfigDict(frozen=True)

    text: str = Field(description="Full extracted text payload")
    pages: list[str] = Field(default_factory=list, description="Text chunked by page")
    tables: list[ParsedTable] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentParserProtocol(Protocol):
    """Protocol for converting raw document bytes into structured ParsedDocument."""

    async def parse(
        self,
        file_content: bytes,
        filename: str,
        content_type: str | None = None,
    ) -> ParsedDocument:
        """Parse raw file bytes into structured document text and metadata."""
        ...
