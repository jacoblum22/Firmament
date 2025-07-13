"""
File validation utilities for secure file upload handling.
"""

import os
from typing import Tuple, Optional
from pathlib import Path


class FileValidationError(Exception):
    """Custom exception for file validation errors"""

    pass


class FileValidator:
    """Comprehensive file validation for upload security"""

    # MIME type mapping for supported file types
    ALLOWED_MIME_TYPES = {
        "pdf": ["application/pdf"],
        "mp3": ["audio/mpeg", "audio/mp3"],
        "wav": ["audio/wav", "audio/x-wav", "audio/wave"],
        "txt": ["text/plain"],
        "m4a": ["audio/mp4", "audio/x-m4a", "audio/aac"],
    }

    # File signatures (magic numbers) for additional security
    FILE_SIGNATURES = {
        "pdf": [b"%PDF-"],
        "mp3": [b"ID3", b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"],
        "wav": [b"RIFF"],
        "txt": [],  # Text files don't have reliable signatures
        "m4a": [b"ftypM4A", b"ftypmp4"],
    }

    # Maximum file sizes per type (in bytes)
    MAX_FILE_SIZES = {
        "pdf": 50 * 1024 * 1024,  # 50MB for PDFs
        "mp3": 200 * 1024 * 1024,  # 200MB for MP3
        "wav": 500 * 1024 * 1024,  # 500MB for WAV (uncompressed)
        "txt": 10 * 1024 * 1024,  # 10MB for text files
        "m4a": 200 * 1024 * 1024,  # 200MB for M4A
    }

    @staticmethod
    def validate_file_extension(filename: str) -> str:
        """
        Validate and extract file extension.

        Args:
            filename: The filename to validate

        Returns:
            str: The validated file extension in lowercase

        Raises:
            FileValidationError: If extension is missing or not allowed
        """
        if not filename:
            raise FileValidationError("Filename is required")

        # Extract extension
        parts = filename.split(".")
        if len(parts) < 2:
            raise FileValidationError("File must have an extension")

        extension = parts[-1].lower()

        if extension not in FileValidator.ALLOWED_MIME_TYPES:
            allowed = ", ".join(
                f".{ext}" for ext in FileValidator.ALLOWED_MIME_TYPES.keys()
            )
            raise FileValidationError(
                f"Unsupported file extension: .{extension}. Allowed: {allowed}"
            )

        return extension

    @staticmethod
    def validate_file_size(
        file_bytes: bytes, extension: str, max_size_override: Optional[int] = None
    ) -> None:
        """
        Validate file size against limits.

        Args:
            file_bytes: The file content as bytes
            extension: The file extension
            max_size_override: Optional override for max size

        Raises:
            FileValidationError: If file is too large
        """
        file_size = len(file_bytes)
        max_size = max_size_override or FileValidator.MAX_FILE_SIZES.get(
            extension, 50 * 1024 * 1024
        )

        if file_size > max_size:
            max_mb = max_size / (1024 * 1024)
            actual_mb = file_size / (1024 * 1024)
            raise FileValidationError(
                f"File too large. Maximum size for .{extension} files: {max_mb:.1f}MB, "
                f"actual size: {actual_mb:.1f}MB"
            )

        if file_size == 0:
            raise FileValidationError("File is empty")

    @staticmethod
    def validate_file_signature(file_bytes: bytes, extension: str) -> None:
        """
        Validate file signature (magic numbers) to prevent file type spoofing.

        Args:
            file_bytes: The file content as bytes
            extension: The expected file extension

        Raises:
            FileValidationError: If file signature doesn't match extension
        """
        if not file_bytes:
            raise FileValidationError("File content is empty")

        signatures = FileValidator.FILE_SIGNATURES.get(extension, [])

        # Skip signature check for text files (no reliable signature)
        if extension == "txt":
            return

        if signatures:
            # Check if file starts with any of the valid signatures
            for signature in signatures:
                if file_bytes.startswith(signature):
                    return

            # Special case for WAV files - check for WAVE in header
            if extension == "wav" and b"WAVE" in file_bytes[:12]:
                return

            # Special case for M4A files - check deeper in header
            if extension == "m4a" and len(file_bytes) > 20:
                header = file_bytes[:20]
                if b"ftyp" in header and (b"M4A" in header or b"mp4" in header):
                    return

            raise FileValidationError(
                f"File content doesn't match .{extension} format. "
                f"File may be corrupted or have incorrect extension."
            )

    @staticmethod
    def validate_filename_security(filename: str) -> None:
        """
        Validate filename for security issues.

        Args:
            filename: The filename to validate

        Raises:
            FileValidationError: If filename contains dangerous characters
        """
        if not filename:
            raise FileValidationError("Filename is required")

        # Check for path traversal attempts
        if ".." in filename or "/" in filename or "\\" in filename:
            raise FileValidationError("Filename contains invalid path characters")

        # Check for null bytes
        if "\x00" in filename:
            raise FileValidationError("Filename contains null bytes")

        # Check filename length
        if len(filename) > 255:
            raise FileValidationError("Filename too long (max 255 characters)")

        # Check for dangerous characters
        dangerous_chars = ["<", ">", ":", '"', "|", "?", "*"]
        for char in dangerous_chars:
            if char in filename:
                raise FileValidationError(
                    f"Filename contains dangerous character: {char}"
                )

    @staticmethod
    def get_safe_filename(filename: str) -> str:
        """
        Generate a safe filename by sanitizing the input.

        Args:
            filename: The original filename

        Returns:
            str: A sanitized, safe filename
        """
        if not filename:
            return "uploaded_file"

        # Remove path components
        filename = os.path.basename(filename)

        # Replace dangerous characters with underscores
        dangerous_chars = ["<", ">", ":", '"', "|", "?", "*", "/", "\\"]
        for char in dangerous_chars:
            filename = filename.replace(char, "_")

        # Remove null bytes
        filename = filename.replace("\x00", "")

        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            max_name_len = 255 - len(ext)
            filename = name[:max_name_len] + ext

        return filename

    @classmethod
    def validate_upload(
        cls, file_bytes: bytes, filename: str, max_size_override: Optional[int] = None
    ) -> Tuple[str, str]:
        """
        Comprehensive file validation for uploads.

        Args:
            file_bytes: The file content as bytes
            filename: The original filename
            max_size_override: Optional override for max file size

        Returns:
            Tuple[str, str]: (validated_extension, safe_filename)

        Raises:
            FileValidationError: If any validation fails
        """
        # 1. Validate filename security
        cls.validate_filename_security(filename)

        # 2. Validate and extract extension
        extension = cls.validate_file_extension(filename)

        # 3. Validate file size
        cls.validate_file_size(file_bytes, extension, max_size_override)

        # 4. Validate file signature
        cls.validate_file_signature(file_bytes, extension)

        # 5. Generate safe filename
        safe_filename = cls.get_safe_filename(filename)

        return extension, safe_filename
