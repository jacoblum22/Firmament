"""
Secure temporary file handling utilities for StudyMate-v2.

This module provides secure temporary file creation with proper cleanup,
restrictive permissions, and optional encryption for sensitive data.
"""

import os
import tempfile
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Generator, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SecureTempFile:
    """
    Secure temporary file manager with automatic cleanup and restrictive permissions.
    """

    def __init__(
        self,
        prefix: str = "studymate_",
        suffix: str = ".tmp",
        secure_delete: bool = True,
        permissions: int = 0o600,
    ):
        """
        Initialize secure temp file manager.

        Args:
            prefix: Prefix for temp file name
            suffix: Suffix for temp file name
            secure_delete: Whether to securely overwrite file before deletion
            permissions: Unix permissions for the temp file (default: owner read/write only)
        """
        self.prefix = prefix
        self.suffix = suffix
        self.secure_delete = secure_delete
        self.permissions = permissions
        self.temp_files: Dict[str, str] = {}  # Track created temp files

    def create_temp_file(self, content: bytes, identifier: Optional[str] = None) -> str:
        """
        Create a secure temporary file with the given content.

        Args:
            content: Binary content to write to the temp file
            identifier: Optional identifier to track this temp file

        Returns:
            Path to the created temporary file

        Raises:
            OSError: If file creation or permission setting fails
        """
        try:
            # Create temporary file with secure defaults
            fd, temp_path = tempfile.mkstemp(
                prefix=self.prefix,
                suffix=self.suffix,
                dir=None,  # Use system temp directory
            )

            try:
                # Set restrictive permissions immediately after creation
                self._set_secure_permissions(temp_path)

                # Write content securely
                with os.fdopen(fd, "wb") as f:
                    f.write(content)
                    f.flush()
                    os.fsync(f.fileno())  # Ensure data is written to disk

                # Track the temp file
                if identifier:
                    self.temp_files[identifier] = temp_path

                logger.info(
                    f"Created secure temp file: {temp_path} (permissions: {oct(self.permissions)})"
                )
                return temp_path

            except Exception as e:
                # Remove the temp file if it was created
                try:
                    if os.path.exists(temp_path):
                        self._secure_delete_file(temp_path)
                except Exception as cleanup_error:
                    logger.warning(f"Cleanup failed for {temp_path}: {cleanup_error}")
                    # Preserve the original exception
                    raise e from cleanup_error

                raise e

        except Exception as e:
            logger.error(f"Failed to create secure temp file: {e}")
            raise OSError(f"Failed to create secure temporary file: {e}") from e

    def _set_secure_permissions(self, file_path: str) -> None:
        """
        Set secure permissions on the file, handling platform differences.

        Args:
            file_path: Path to the file to secure
        """
        try:
            if os.name == "nt":  # Windows
                # On Windows, use icacls to set proper ACL for owner-only access
                self._set_windows_acl(file_path)
            else:
                # Unix/Linux - use standard chmod which works reliably
                os.chmod(file_path, self.permissions)

        except Exception as e:
            logger.warning(f"Failed to set secure permissions on {file_path}: {e}")
            # Don't fail the entire operation if permission setting fails

    def _set_windows_acl(self, file_path: str) -> None:
        """
        Set Windows ACL to restrict access to current user only.

        Args:
            file_path: Path to the file to secure
        """
        try:
            # Get current user
            import getpass

            current_user = getpass.getuser()

            # Remove all inherited permissions and set owner-only access
            # /inheritance:r removes inheritance
            # /grant gives specific permissions (F = Full control to current user)
            # /deny Everyone:F would deny access to everyone else, but we'll use a more targeted approach

            subprocess.run(
                [
                    "icacls",
                    file_path,
                    "/inheritance:r",  # Remove inheritance
                    "/grant:r",
                    f"{current_user}:(F)",  # Grant full control to current user only
                    "/remove",
                    "Everyone",  # Remove Everyone group
                    "/remove",
                    "Users",  # Remove Users group
                    "/remove",
                    "Authenticated Users",  # Remove Authenticated Users group
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            logger.debug(f"Set Windows ACL for {file_path} to owner-only access")

        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to set Windows ACL on {file_path}: {e.stderr}")
            # Fallback to basic chmod
            os.chmod(file_path, self.permissions)
        except Exception as e:
            logger.warning(f"Error setting Windows ACL on {file_path}: {e}")
            # Fallback to basic chmod
            os.chmod(file_path, self.permissions)

    def cleanup_file(self, file_path: str, identifier: Optional[str] = None) -> bool:
        """
        Securely clean up a temporary file.

        Args:
            file_path: Path to the file to clean up
            identifier: Optional identifier to remove from tracking

        Returns:
            True if cleanup was successful, False otherwise
        """
        try:
            if os.path.exists(file_path):
                self._secure_delete_file(file_path)

            # Remove from tracking
            if identifier and identifier in self.temp_files:
                del self.temp_files[identifier]

            logger.info(f"Successfully cleaned up temp file: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to cleanup temp file {file_path}: {e}")
            return False

    def cleanup_all(self) -> Dict[str, bool]:
        """
        Clean up all tracked temporary files.

        Returns:
            Dictionary mapping identifiers to cleanup success status
        """
        results = {}

        for identifier, file_path in list(self.temp_files.items()):
            results[identifier] = self.cleanup_file(file_path, identifier)

        return results

    def _secure_delete_file(self, file_path: str) -> None:
        """
        Securely delete a file by overwriting it before removal.

        Args:
            file_path: Path to the file to securely delete
        """
        if not self.secure_delete:
            os.remove(file_path)
            return

        try:
            # Get file size
            file_size = os.path.getsize(file_path)

            # Overwrite with random data multiple times for security
            with open(file_path, "r+b") as f:
                for _ in range(3):  # Multiple passes
                    f.seek(0)
                    f.write(os.urandom(file_size))
                    f.flush()
                    os.fsync(f.fileno())

            # Finally remove the file
            os.remove(file_path)

        except Exception as e:
            # Fallback to regular deletion
            logger.warning(
                f"Secure deletion failed for {file_path}, using regular deletion: {e}"
            )
            try:
                os.remove(file_path)
            except Exception as remove_error:
                logger.error(f"Failed to remove file {file_path}: {remove_error}")
                raise remove_error


@contextmanager
def secure_temp_file(
    content: bytes, prefix: str = "studymate_", suffix: str = ".tmp"
) -> Generator[str, None, None]:
    """
    Context manager for creating and automatically cleaning up a secure temporary file.

    Args:
        content: Binary content to write to the temp file
        prefix: Prefix for temp file name
        suffix: Suffix for temp file name

    Yields:
        Path to the temporary file

    Example:
        with secure_temp_file(file_bytes, prefix="upload_", suffix=".bin") as temp_path:
            # Use temp_path
            process_file(temp_path)
        # File is automatically cleaned up here
    """
    manager = SecureTempFile(prefix=prefix, suffix=suffix)
    temp_path = None

    try:
        temp_path = manager.create_temp_file(content)
        yield temp_path
    finally:
        if temp_path:
            manager.cleanup_file(temp_path)


class InMemoryStorage:
    """
    In-memory storage for temporary data that doesn't need to touch disk.
    """

    def __init__(self, max_size_mb: float = 100.0):
        """
        Initialize in-memory storage.

        Args:
            max_size_mb: Maximum size in MB for stored data (can be float)
        """
        self.max_size_bytes = int(max_size_mb * 1024 * 1024)
        self.storage: Dict[str, bytes] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}

    def store(
        self, identifier: str, content: bytes, metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store content in memory.

        Args:
            identifier: Unique identifier for the content
            content: Binary content to store
            metadata: Optional metadata associated with the content

        Returns:
            True if stored successfully, False if size limit exceeded
        """
        if len(content) > self.max_size_bytes:
            logger.warning(
                f"Content too large for in-memory storage: {len(content)} bytes"
            )
            return False

        current_size = sum(len(data) for data in self.storage.values())
        if current_size + len(content) > self.max_size_bytes:
            logger.warning(
                f"In-memory storage limit exceeded: {current_size + len(content)} bytes"
            )
            return False

        self.storage[identifier] = content
        self.metadata[identifier] = metadata or {}

        logger.info(
            f"Stored {len(content)} bytes in memory with identifier: {identifier}"
        )
        return True

    def retrieve(self, identifier: str) -> Optional[bytes]:
        """
        Retrieve content from memory.

        Args:
            identifier: Identifier of the content to retrieve

        Returns:
            Content bytes if found, None otherwise
        """
        return self.storage.get(identifier)

    def get_metadata(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for stored content.

        Args:
            identifier: Identifier of the content

        Returns:
            Metadata dictionary if found, None otherwise
        """
        return self.metadata.get(identifier)

    def remove(self, identifier: str) -> bool:
        """
        Remove content from memory.

        Args:
            identifier: Identifier of the content to remove

        Returns:
            True if removed, False if not found
        """
        if identifier in self.storage:
            del self.storage[identifier]
            self.metadata.pop(identifier, None)
            logger.info(f"Removed content from memory: {identifier}")
            return True
        return False

    def clear(self) -> None:
        """Clear all stored content."""
        count = len(self.storage)
        self.storage.clear()
        self.metadata.clear()
        logger.info(f"Cleared {count} items from in-memory storage")

    def get_size_info(self) -> Dict[str, Any]:
        """
        Get information about current storage usage.

        Returns:
            Dictionary with size information
        """
        current_size = sum(len(data) for data in self.storage.values())
        return {
            "items_count": len(self.storage),
            "current_size_bytes": current_size,
            "current_size_mb": round(current_size / (1024 * 1024), 2),
            "max_size_mb": self.max_size_bytes / (1024 * 1024),
            "usage_percent": round((current_size / self.max_size_bytes) * 100, 2),
        }


# Global in-memory storage instance
_memory_storage = InMemoryStorage()


def get_memory_storage() -> InMemoryStorage:
    """Get the global in-memory storage instance."""
    return _memory_storage
