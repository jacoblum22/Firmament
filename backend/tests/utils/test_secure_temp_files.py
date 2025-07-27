"""
Test cases for secure temporary file handling improvements.
"""

import os
import subprocess
import getpass
import pytest

from utils.secure_temp_files import (
    SecureTempFile,
    secure_temp_file,
    InMemoryStorage,
    get_memory_storage,
)


class TestSecureTempFile:
    """Test secure temporary file functionality."""

    def _verify_windows_acl_security(self, file_path: str) -> None:
        """
        Verify that Windows ACL restricts access to current user only.

        Args:
            file_path: Path to the file to check
        """
        try:
            # Get ACL information using icacls
            result = subprocess.run(
                ["icacls", file_path], capture_output=True, text=True, check=True
            )

            acl_output = result.stdout
            current_user = getpass.getuser()

            # Check that only the current user has permissions
            lines = acl_output.strip().split("\n")
            permission_line = lines[0] if lines else ""

            # Should contain current user with permissions, and no other users
            assert (
                current_user in permission_line
            ), f"Current user {current_user} not found in ACL: {permission_line}"

            # Should not contain common insecure groups
            insecure_patterns = ["Everyone:", "Users:", "Authenticated Users:"]
            for pattern in insecure_patterns:
                assert (
                    pattern not in acl_output
                ), f"Insecure permission found: {pattern} in ACL output: {acl_output}"

        except subprocess.CalledProcessError as e:
            pytest.fail(f"Failed to check Windows ACL: {e.stderr}")
        except Exception as e:
            pytest.fail(f"Error checking Windows ACL: {e}")

    def test_create_secure_temp_file(self):
        """Test creating a secure temporary file with restricted permissions."""
        manager = SecureTempFile(prefix="test_", suffix=".bin")
        test_content = b"test content for secure file"

        temp_path = manager.create_temp_file(test_content, "test_id")

        try:
            # Verify file exists and has content
            assert os.path.exists(temp_path)
            with open(temp_path, "rb") as f:
                assert f.read() == test_content

            # Verify restrictive permissions
            file_stat = os.stat(temp_path)
            permissions = oct(file_stat.st_mode)[-3:]  # Get last 3 digits

            if os.name == "nt":  # Windows
                # On Windows, verify ACL security instead of Unix permissions
                self._verify_windows_acl_security(temp_path)
            else:  # Unix/Linux
                # On Unix, check traditional permissions
                assert (
                    permissions == "600"
                ), f"Expected '600' (owner read/write only) on Unix, got '{permissions}'"

        finally:
            # Cleanup
            manager.cleanup_file(temp_path, "test_id")
            assert not os.path.exists(temp_path)

    def test_secure_cleanup(self):
        """Test secure deletion of temporary files."""
        manager = SecureTempFile(secure_delete=True)
        test_content = b"sensitive data that should be securely deleted"

        temp_path = manager.create_temp_file(test_content)
        assert os.path.exists(temp_path)

        # Cleanup should securely delete the file
        assert manager.cleanup_file(temp_path)
        assert not os.path.exists(temp_path)

    def test_context_manager(self):
        """Test the secure temp file context manager."""
        test_content = b"context manager test content"

        temp_path = None
        with secure_temp_file(test_content, prefix="ctx_", suffix=".test") as path:
            temp_path = path
            assert os.path.exists(path)

            with open(path, "rb") as f:
                assert f.read() == test_content

        # File should be automatically cleaned up
        assert not os.path.exists(temp_path)

    def test_cleanup_all(self):
        """Test cleaning up all tracked temporary files."""
        manager = SecureTempFile()

        # Create multiple temp files
        content1 = b"file 1 content"
        content2 = b"file 2 content"

        path1 = manager.create_temp_file(content1, "file1")
        path2 = manager.create_temp_file(content2, "file2")

        assert os.path.exists(path1)
        assert os.path.exists(path2)

        # Cleanup all
        results = manager.cleanup_all()

        assert results["file1"] is True
        assert results["file2"] is True
        assert not os.path.exists(path1)
        assert not os.path.exists(path2)


class TestInMemoryStorage:
    """Test in-memory storage functionality."""

    def test_store_and_retrieve(self):
        """Test storing and retrieving content from memory."""
        storage = InMemoryStorage(max_size_mb=1)
        test_content = b"test content for memory storage"

        # Store content
        assert storage.store("test_key", test_content, {"type": "test"})

        # Retrieve content
        retrieved = storage.retrieve("test_key")
        assert retrieved == test_content

        # Check metadata
        metadata = storage.get_metadata("test_key")
        assert metadata is not None, "Metadata should not be None"
        assert metadata["type"] == "test"

    def test_size_limits(self):
        """Test memory storage size limits."""
        storage = InMemoryStorage(
            max_size_mb=0.001
        )  # Very small limit (1KB) to test size restrictions
        large_content = b"x" * 2048  # 2KB content

        # Should fail due to size limit
        assert not storage.store("large_key", large_content)

    def test_clear_storage(self):
        """Test clearing all stored content."""
        storage = InMemoryStorage()

        storage.store("key1", b"content1")
        storage.store("key2", b"content2")

        assert storage.retrieve("key1") is not None
        assert storage.retrieve("key2") is not None

        storage.clear()

        assert storage.retrieve("key1") is None
        assert storage.retrieve("key2") is None

    def test_size_info(self):
        """Test getting storage size information."""
        storage = InMemoryStorage(
            max_size_mb=0.001
        )  # Use very small max size (1KB) to ensure percentage is > 0
        test_content = b"test content"

        storage.store("test", test_content)

        info = storage.get_size_info()
        assert info["items_count"] == 1
        assert info["current_size_bytes"] == len(test_content)
        assert info["usage_percent"] > 0


class TestFilePermissions:
    """Test file permission security."""

    @pytest.mark.skipif(
        os.name == "nt", reason="Unix permissions not applicable on Windows"
    )
    def test_unix_permissions(self):
        """Test that files are created with secure Unix permissions."""
        manager = SecureTempFile(permissions=0o600)
        temp_path = manager.create_temp_file(b"test")

        try:
            stat_info = os.stat(temp_path)
            # Check that only owner has read/write permissions
            assert stat_info.st_mode & 0o777 == 0o600
        finally:
            manager.cleanup_file(temp_path)

    def test_windows_permissions(self):
        """Test that files are created with appropriate Windows permissions."""
        if os.name != "nt":
            pytest.skip("Windows-specific test")

        manager = SecureTempFile()
        temp_path = manager.create_temp_file(b"test")

        try:
            # On Windows, verify file exists and is accessible
            assert os.path.exists(temp_path)
            assert os.access(temp_path, os.R_OK | os.W_OK)
        finally:
            manager.cleanup_file(temp_path)


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_invalid_content(self):
        """Test handling of invalid content."""
        manager = SecureTempFile()

        # Should handle empty content gracefully
        temp_path = manager.create_temp_file(b"")
        assert os.path.exists(temp_path)
        manager.cleanup_file(temp_path)

    def test_cleanup_nonexistent_file(self):
        """Test cleanup of non-existent file."""
        manager = SecureTempFile()

        # Should not raise error for non-existent file
        result = manager.cleanup_file("/nonexistent/path/file.tmp")
        assert result is True  # Should return True even if file doesn't exist

    def test_storage_retrieval_nonexistent(self):
        """Test retrieving non-existent content from memory storage."""
        storage = InMemoryStorage()

        result = storage.retrieve("nonexistent_key")
        assert result is None


def test_integration_scenario():
    """Test a realistic integration scenario."""
    # Simulate file upload processing
    file_content = b"This is simulated file content that needs secure handling"
    job_id = "test_job_123"
    content_hash = "abc123def456"

    # Try memory storage first
    memory_storage = get_memory_storage()
    storage_key = f"{job_id}_{content_hash}"

    if memory_storage.store(storage_key, file_content, {"job_id": job_id}):
        # Memory storage succeeded
        retrieved_content = memory_storage.retrieve(storage_key)
        assert retrieved_content == file_content

        # Cleanup
        assert memory_storage.remove(storage_key)
        assert memory_storage.retrieve(storage_key) is None

    else:
        # Fallback to secure temp file
        with secure_temp_file(
            file_content, prefix=f"job_{job_id}_", suffix=".bin"
        ) as temp_path:
            # Verify file exists and has correct content
            assert os.path.exists(temp_path)
            with open(temp_path, "rb") as f:
                assert f.read() == file_content
        # File is automatically cleaned up after context


if __name__ == "__main__":
    pytest.main([__file__])
