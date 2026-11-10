"""
Abstract document and blob storage port.

Defines the contract for storing and retrieving raw binary artifacts (e.g. Azure Blob Storage).
"""
from typing import Protocol


class DocumentStorageProtocol(Protocol):
    """Protocol for binary object and document file storage."""

    async def upload(
        self,
        file_path: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload raw binary data and return its persistent storage URI/path."""
        ...

    async def download(self, file_path: str) -> bytes:
        """Download binary file data by path or key."""
        ...

    async def delete(self, file_path: str) -> bool:
        """Delete a file from object storage."""
        ...

    async def get_url(
        self,
        file_path: str,
        expires_in_seconds: int = 3600,
    ) -> str:
        """Generate a secure, time-limited download URL (e.g., Azure SAS token)."""
        ...
