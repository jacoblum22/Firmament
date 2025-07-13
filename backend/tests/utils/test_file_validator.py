"""
Tests for file validation utilities.
"""

import pytest
from utils.file_validator import FileValidator, FileValidationError


class TestFileValidator:
    """Test the FileValidator class"""

    def test_validate_file_extension_valid(self):
        """Test validation of valid file extensions"""
        assert FileValidator.validate_file_extension("test.pdf") == "pdf"
        assert FileValidator.validate_file_extension("audio.mp3") == "mp3"
        assert FileValidator.validate_file_extension("recording.wav") == "wav"
        assert FileValidator.validate_file_extension("document.txt") == "txt"
        assert FileValidator.validate_file_extension("music.m4a") == "m4a"

    def test_validate_file_extension_case_insensitive(self):
        """Test that extension validation is case insensitive"""
        assert FileValidator.validate_file_extension("test.PDF") == "pdf"
        assert FileValidator.validate_file_extension("audio.MP3") == "mp3"

    def test_validate_file_extension_invalid(self):
        """Test validation of invalid file extensions"""
        with pytest.raises(FileValidationError, match="Unsupported file extension"):
            FileValidator.validate_file_extension("malware.exe")

        with pytest.raises(FileValidationError, match="Unsupported file extension"):
            FileValidator.validate_file_extension("archive.zip")

    def test_validate_file_extension_missing(self):
        """Test validation of files without extensions"""
        with pytest.raises(FileValidationError, match="File must have an extension"):
            FileValidator.validate_file_extension("filename")

        with pytest.raises(FileValidationError, match="Filename is required"):
            FileValidator.validate_file_extension("")

    def test_validate_file_extension_multiple_dots(self):
        """Test that extension validation works correctly with filenames containing multiple dots"""
        # These should all work correctly with os.path.splitext approach
        assert (
            FileValidator.validate_file_extension("my.document.with.dots.pdf") == "pdf"
        )
        assert FileValidator.validate_file_extension("version.1.2.backup.txt") == "txt"
        assert FileValidator.validate_file_extension("audio.track.01.mp3") == "mp3"
        assert (
            FileValidator.validate_file_extension("data.export.2024.01.15.wav") == "wav"
        )
        assert FileValidator.validate_file_extension("config.dev.local.m4a") == "m4a"

        # Hidden files should work
        assert FileValidator.validate_file_extension(".hidden.file.pdf") == "pdf"

        # Files ending with double dots should still work
        assert FileValidator.validate_file_extension("file..pdf") == "pdf"

    def test_validate_file_extension_edge_cases(self):
        """Test edge cases for file extension validation"""
        # File ending with just a dot should fail
        with pytest.raises(
            FileValidationError, match="File must have a valid extension"
        ):
            FileValidator.validate_file_extension("filename.")

        # File starting with dot but no extension should fail
        with pytest.raises(FileValidationError, match="File must have an extension"):
            FileValidator.validate_file_extension(".hidden_no_ext")

        # Empty filename should fail
        with pytest.raises(FileValidationError, match="Filename is required"):
            FileValidator.validate_file_extension("")

    def test_validate_file_size_valid(self):
        """Test validation of valid file sizes"""
        # Small PDF file
        small_pdf = b"small content"
        FileValidator.validate_file_size(small_pdf, "pdf")

        # Medium audio file
        medium_audio = b"x" * (10 * 1024 * 1024)  # 10MB
        FileValidator.validate_file_size(medium_audio, "mp3")

    def test_validate_file_size_too_large(self):
        """Test validation of files that are too large"""
        # Large PDF (over 50MB limit)
        large_pdf = b"x" * (60 * 1024 * 1024)  # 60MB
        with pytest.raises(FileValidationError, match="File too large"):
            FileValidator.validate_file_size(large_pdf, "pdf")

    def test_validate_file_size_empty(self):
        """Test validation of empty files"""
        with pytest.raises(FileValidationError, match="File is empty"):
            FileValidator.validate_file_size(b"", "pdf")

    def test_validate_file_size_with_override(self):
        """Test file size validation with custom size limit"""
        # 1MB file with 500KB limit
        large_file = b"x" * (1024 * 1024)  # 1MB
        with pytest.raises(FileValidationError, match="File too large"):
            FileValidator.validate_file_size(
                large_file, "pdf", 500 * 1024
            )  # 500KB limit

    def test_validate_file_signature_pdf(self):
        """Test PDF file signature validation"""
        # Valid PDF signature
        pdf_content = b"%PDF-1.4\n%some pdf content"
        FileValidator.validate_file_signature(pdf_content, "pdf")

        # Invalid PDF signature
        fake_pdf = b"not a pdf file"
        with pytest.raises(FileValidationError, match="File content doesn't match"):
            FileValidator.validate_file_signature(fake_pdf, "pdf")

    def test_validate_file_signature_mp3(self):
        """Test MP3 file signature validation"""
        # Valid MP3 signatures
        mp3_id3 = b"ID3\x03\x00\x00\x00"
        FileValidator.validate_file_signature(mp3_id3, "mp3")

        mp3_frame = b"\xff\xfb\x90\x00"
        FileValidator.validate_file_signature(mp3_frame, "mp3")

    def test_validate_file_signature_wav(self):
        """Test WAV file signature validation"""
        # Valid WAV signature
        wav_content = b"RIFF\x24\x08\x00\x00WAVE"
        FileValidator.validate_file_signature(wav_content, "wav")

    def test_validate_file_signature_txt(self):
        """Test that text files skip signature validation"""
        # Text files should pass signature validation regardless of content
        FileValidator.validate_file_signature(b"any text content", "txt")
        FileValidator.validate_file_signature(b"\xff\xfe", "txt")  # Even binary data

    def test_validate_filename_security_valid(self):
        """Test validation of safe filenames"""
        FileValidator.validate_filename_security("document.pdf")
        FileValidator.validate_filename_security("my_audio_file.mp3")
        FileValidator.validate_filename_security("lecture-notes.txt")

    def test_validate_filename_security_path_traversal(self):
        """Test detection of path traversal attempts"""
        with pytest.raises(FileValidationError, match="invalid path characters"):
            FileValidator.validate_filename_security("../../../etc/passwd")

        with pytest.raises(FileValidationError, match="invalid path characters"):
            FileValidator.validate_filename_security("folder/file.pdf")

    def test_validate_filename_security_dangerous_chars(self):
        """Test detection of dangerous characters"""
        dangerous_names = ["file<script>.pdf", "file>output.txt", "file|pipe.mp3"]
        for name in dangerous_names:
            with pytest.raises(FileValidationError, match="dangerous character"):
                FileValidator.validate_filename_security(name)

    def test_validate_filename_security_null_bytes(self):
        """Test detection of null bytes"""
        with pytest.raises(FileValidationError, match="null bytes"):
            FileValidator.validate_filename_security("file\x00.pdf")

    def test_validate_filename_security_too_long(self):
        """Test detection of overly long filenames"""
        long_name = "a" * 260 + ".pdf"
        with pytest.raises(FileValidationError, match="Filename too long"):
            FileValidator.validate_filename_security(long_name)

    def test_get_safe_filename(self):
        """Test filename sanitization"""
        assert FileValidator.get_safe_filename("normal.pdf") == "normal.pdf"
        assert FileValidator.get_safe_filename("file<script>.pdf") == "file_script_.pdf"
        assert (
            FileValidator.get_safe_filename("../../../malicious.txt") == "malicious.txt"
        )  # os.path.basename removes path
        assert (
            FileValidator.get_safe_filename("file:with|dangerous*chars.txt")
            == "file_with_dangerous_chars.txt"
        )
        assert FileValidator.get_safe_filename("") == "uploaded_file"

    def test_validate_upload_comprehensive(self):
        """Test comprehensive upload validation"""
        # Valid PDF upload
        pdf_content = b"%PDF-1.4\nsome pdf content here"
        ext, safe_name = FileValidator.validate_upload(pdf_content, "document.pdf")
        assert ext == "pdf"
        assert safe_name == "document.pdf"

    def test_validate_upload_security_issues(self):
        """Test that upload validation catches security issues"""
        # Path traversal attempt
        pdf_content = b"%PDF-1.4\nsome content"
        with pytest.raises(FileValidationError, match="invalid path characters"):
            FileValidator.validate_upload(pdf_content, "../../../malicious.pdf")

    def test_validate_upload_malformed_file(self):
        """Test validation of malformed files"""
        # File with wrong extension
        fake_pdf = b"not a real pdf file"
        with pytest.raises(FileValidationError, match="File content doesn't match"):
            FileValidator.validate_upload(fake_pdf, "document.pdf")

    def test_validate_upload_oversized_file(self):
        """Test validation of oversized files"""
        # Create a file larger than PDF limit (50MB)
        large_content = b"x" * (60 * 1024 * 1024)  # 60MB
        with pytest.raises(FileValidationError, match="File too large"):
            FileValidator.validate_upload(large_content, "large.pdf")

    def test_file_type_specific_limits(self):
        """Test that different file types have appropriate size limits"""
        # Create files at the boundary of each type's limit

        # PDF: 50MB limit
        pdf_limit = FileValidator.MAX_FILE_SIZES["pdf"]
        assert pdf_limit == 50 * 1024 * 1024

        # Audio files: larger limits
        mp3_limit = FileValidator.MAX_FILE_SIZES["mp3"]
        wav_limit = FileValidator.MAX_FILE_SIZES["wav"]
        assert mp3_limit == 200 * 1024 * 1024
        assert wav_limit == 500 * 1024 * 1024  # WAV files are larger (uncompressed)

        # Text files: smaller limit
        txt_limit = FileValidator.MAX_FILE_SIZES["txt"]
        assert txt_limit == 10 * 1024 * 1024
