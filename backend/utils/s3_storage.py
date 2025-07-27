"""
AWS S3 Storage Utilities for StudyMate

This module provides utilities for uploading, downloading, and managing files in AWS S3.
It supports both local development (with fallback to local storage) and production S3 usage.
"""

import os
import logging
import threading
from pathlib import Path
from typing import Optional, BinaryIO, Union, Any
from io import BytesIO
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from config import Settings

logger = logging.getLogger(__name__)


class S3StorageManager:
    """Manages file storage operations with AWS S3 and local fallback"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.s3_client = None
        self.use_s3 = settings.use_s3_storage

        if self.use_s3:
            try:
                self.s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key,
                    region_name=settings.aws_region,
                )
                # Test the connection
                self.s3_client.head_bucket(Bucket=settings.s3_bucket_name)
                logger.info(
                    f"✓ S3 storage initialized successfully (bucket: {settings.s3_bucket_name})"
                )
            except (ClientError, NoCredentialsError) as e:
                logger.warning(
                    f"⚠️  S3 initialization failed: {e}. Falling back to local storage."
                )
                self.use_s3 = False
                self.s3_client = None
        else:
            logger.info("📁 Using local file storage")

    def _validate_key(self, key: str) -> None:
        """Validate key for security and format"""
        if not key or not isinstance(key, str):
            raise ValueError("Key must be a non-empty string")

        # Check for path traversal attempts (including encoded versions)
        dangerous_patterns = [
            "..",  # Standard path traversal
            "%2e%2e",  # URL encoded ..
            "%5c",  # URL encoded backslash \
            "..%2f",  # Mixed encoding ../
            "%2e%2e%2f",  # Fully encoded ../
            "%2e%2e%5c",  # Fully encoded ..\
        ]

        key_lower = key.lower()
        for pattern in dangerous_patterns:
            if pattern in key_lower:
                raise ValueError(f"Invalid key format (path traversal attempt): {key}")

        # Check for absolute paths and backslashes (Windows paths)
        if key.startswith("/") or "\\" in key:
            raise ValueError(f"Invalid key format (absolute path or backslash): {key}")

        # Check for null bytes and other dangerous characters
        dangerous_chars = ["\x00", "<", ">", ":", '"', "|", "?", "*"]
        if any(c in key for c in dangerous_chars):
            raise ValueError(f"Key contains invalid characters: {key}")

        # Additional security checks
        if key.startswith("-"):  # Prevent command injection in shell operations
            raise ValueError(f"Key cannot start with dash: {key}")

        # Check for control characters (0x00-0x1F and 0x7F-0x9F)
        if any(ord(c) < 32 or (127 <= ord(c) <= 159) for c in key):
            raise ValueError(f"Key contains control characters: {key}")

        # Ensure reasonable length
        if len(key) > 1024:
            raise ValueError(f"Key too long: {len(key)} characters")

    def _get_local_path(self, key: str) -> Path:
        """Get local file path for a given key"""
        # Validate key to prevent path traversal attacks
        self._validate_key(key)

        # Remove S3 prefixes and create local equivalent
        clean_key = key.replace(self.settings.s3_uploads_prefix, "uploads/")
        clean_key = clean_key.replace(self.settings.s3_cache_prefix, "cache/")
        clean_key = clean_key.replace(self.settings.s3_temp_prefix, "temp_chunks/")

        # Use absolute paths based on application base directory, not CWD
        base_dir = Path(__file__).parent.parent.resolve()  # backend directory
        local_path = base_dir / clean_key

        # Ensure the resolved path is within expected directories
        try:
            local_path_resolved = local_path.resolve()

            allowed_dirs = [
                base_dir / self.settings.upload_directory,
                base_dir / "cache",
                base_dir / self.settings.temp_directory,
            ]
            # Resolve all allowed directories to absolute paths
            allowed_dirs = [d.resolve() for d in allowed_dirs]

            # Use proper path validation instead of string comparison
            is_safe = any(
                local_path_resolved.is_relative_to(allowed_dir)
                for allowed_dir in allowed_dirs
            )

            if not is_safe:
                raise ValueError(
                    f"Path outside allowed directories: {local_path_resolved}"
                )

        except (OSError, ValueError) as e:
            raise ValueError(f"Invalid path: {e}")

        local_path.parent.mkdir(parents=True, exist_ok=True)
        return local_path

    def upload_file(
        self, file_data: Any, key: str, content_type: Optional[str] = None
    ) -> bool:
        """
        Upload a file to S3 or local storage

        Args:
            file_data: File content as bytes/bytearray or file-like object
            key: S3 key or local file path
            content_type: MIME type of the file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate the key first
            self._validate_key(key)

            # Convert file_data to bytes for consistent handling
            if isinstance(file_data, bytes):
                data_bytes = file_data
            elif isinstance(file_data, bytearray):
                data_bytes = bytes(file_data)
            elif hasattr(file_data, "read"):
                # File-like object
                if hasattr(file_data, "seek"):
                    file_data.seek(0)
                data_bytes = file_data.read()
                if not isinstance(data_bytes, bytes):
                    if isinstance(data_bytes, str):
                        data_bytes = data_bytes.encode("utf-8")
                    else:
                        data_bytes = bytes(data_bytes)
            else:
                # Last resort: try to convert to bytes
                try:
                    data_bytes = bytes(file_data)
                except (TypeError, ValueError) as e:
                    logger.error(f"❌ Cannot convert file_data to bytes: {e}")
                    return False

            if self.use_s3 and self.s3_client:
                # Upload to S3
                extra_args = {}
                if content_type:
                    extra_args["ContentType"] = content_type

                file_obj = BytesIO(data_bytes)
                self.s3_client.upload_fileobj(
                    file_obj, self.settings.s3_bucket_name, key, ExtraArgs=extra_args
                )
                logger.debug(f"✓ Uploaded to S3: {key}")
                return True
            else:
                # Save to local storage
                local_path = self._get_local_path(key)
                local_path.write_bytes(data_bytes)
                logger.debug(f"✓ Saved locally: {local_path}")
                return True

        except Exception as e:
            logger.error(f"❌ Failed to upload {key}: {e}")
            return False

    def download_file(self, key: str) -> Optional[bytes]:
        """
        Download a file from S3 or local storage

        Args:
            key: S3 key or local file path

        Returns:
            bytes: File content if successful, None otherwise
        """
        try:
            # Validate the key first
            self._validate_key(key)

            if self.use_s3 and self.s3_client:
                # Download from S3
                response = self.s3_client.get_object(
                    Bucket=self.settings.s3_bucket_name, Key=key
                )
                content = response["Body"].read()
                logger.debug(f"✓ Downloaded from S3: {key}")
                return content
            else:
                # Read from local storage
                local_path = self._get_local_path(key)
                if local_path.exists():
                    content = local_path.read_bytes()
                    logger.debug(f"✓ Read locally: {local_path}")
                    return content
                else:
                    logger.warning(f"⚠️  Local file not found: {local_path}")
                    return None

        except Exception as e:
            logger.error(f"❌ Failed to download {key}: {e}")
            return None

    def file_exists(self, key: str) -> bool:
        """
        Check if a file exists in S3 or local storage

        Args:
            key: S3 key or local file path

        Returns:
            bool: True if file exists, False otherwise
        """
        try:
            # Validate the key first
            self._validate_key(key)
            if self.use_s3 and self.s3_client:
                # Check S3
                self.s3_client.head_object(Bucket=self.settings.s3_bucket_name, Key=key)
                return True
            else:
                # Check local storage
                local_path = self._get_local_path(key)
                return local_path.exists()

        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            else:
                logger.error(f"❌ Error checking file existence {key}: {e}")
                return False
        except Exception as e:
            logger.error(f"❌ Error checking file existence {key}: {e}")
            return False

    def delete_file(self, key: str) -> bool:
        """
        Delete a file from S3 or local storage

        Args:
            key: S3 key or local file path

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate the key first
            self._validate_key(key)

            if self.use_s3 and self.s3_client:
                # Delete from S3
                self.s3_client.delete_object(
                    Bucket=self.settings.s3_bucket_name, Key=key
                )
                logger.debug(f"✓ Deleted from S3: {key}")
                return True
            else:
                # Delete from local storage
                local_path = self._get_local_path(key)
                if local_path.exists():
                    local_path.unlink()
                    logger.debug(f"✓ Deleted locally: {local_path}")
                return True

        except Exception as e:
            logger.error(f"❌ Failed to delete {key}: {e}")
            return False

    def list_files(self, prefix: str = "") -> list[str]:
        """
        List files with a given prefix

        Args:
            prefix: Key prefix to filter by

        Returns:
            list[str]: List of file keys
        """
        try:
            if self.use_s3 and self.s3_client:
                # List from S3 with pagination support
                files = []
                paginator = self.s3_client.get_paginator("list_objects_v2")
                page_iterator = paginator.paginate(
                    Bucket=self.settings.s3_bucket_name, Prefix=prefix
                )
                for page in page_iterator:
                    files.extend([obj["Key"] for obj in page.get("Contents", [])])
                return files
            else:
                # List from local storage
                local_prefix = self._get_local_path(prefix)
                if local_prefix.is_dir():
                    files = []
                    for file_path in local_prefix.rglob("*"):
                        if file_path.is_file():
                            # Calculate relative path from the backend directory (consistent regardless of CWD)
                            base_dir = Path(
                                __file__
                            ).parent.parent.resolve()  # backend directory
                            try:
                                relative_path = file_path.relative_to(base_dir)
                                key = str(relative_path).replace("\\", "/")
                                files.append(key)
                            except ValueError:
                                # Skip files that can't be made relative to base_path
                                logger.warning(
                                    f"Skipping file outside base path: {file_path}"
                                )
                                continue
                    return files
                return []

        except Exception as e:
            logger.error(f"❌ Failed to list files with prefix {prefix}: {e}")
            return []

    def get_file_url(self, key: str, expires_in: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for accessing a file

        Args:
            key: S3 key
            expires_in: URL expiration time in seconds

        Returns:
            str: Presigned URL if using S3, None for local storage
        """
        try:
            # Validate the key first
            self._validate_key(key)

            if self.use_s3 and self.s3_client:
                url = self.s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.settings.s3_bucket_name, "Key": key},
                    ExpiresIn=expires_in,
                )
                return url
            else:
                # For local storage, we'll need to serve files through the API
                return None

        except Exception as e:
            logger.error(f"❌ Failed to generate presigned URL for {key}: {e}")
            return None


# Global storage manager instance
_storage_manager: Optional[S3StorageManager] = None
_lock = threading.Lock()


def get_storage_manager(settings: Optional[Settings] = None) -> S3StorageManager:
    """Get the global storage manager instance (thread-safe)"""
    global _storage_manager

    if _storage_manager is None:
        with _lock:
            if _storage_manager is None:
                if settings is None:
                    settings = Settings()
                _storage_manager = S3StorageManager(settings)
    return _storage_manager


def init_storage_manager(settings: Settings) -> S3StorageManager:
    """Initialize the global storage manager with specific settings (thread-safe)"""
    global _storage_manager
    with _lock:
        _storage_manager = S3StorageManager(settings)
    return _storage_manager
