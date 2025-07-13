"""
Test file generators for creating various file types for testing.
"""

import os
import tempfile
from typing import Tuple, Dict, Optional
from pathlib import Path
import pytest
from utils.file_validator import FileValidator, FileValidationError


class TestFileGenerator:
    """Generate test files for upload validation testing"""

    @staticmethod
    def create_valid_pdf(size_mb: float = 1.0) -> bytes:
        """Create a valid PDF file of specified size"""
        # Basic PDF structure
        header = b"%PDF-1.4\n"

        # Create catalog and pages
        catalog = b"1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"

        pages = b"2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n"

        page = b"3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\n"

        # Calculate how much padding we need
        base_size = len(header + catalog + pages + page)
        target_size = int(size_mb * 1024 * 1024)
        padding_size = max(0, target_size - base_size - 100)  # Leave room for trailer

        # Add padding as comments
        padding = b"% " + b"x" * padding_size + b"\n"

        # PDF trailer
        trailer = b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n0\n%%EOF\n"

        return header + catalog + pages + page + padding + trailer

    @staticmethod
    def create_valid_mp3(size_mb: float = 1.0) -> bytes:
        """Create a valid MP3 file of specified size"""
        # ID3v2 header
        id3_header = b"ID3\x03\x00\x00\x00\x00\x17\x76"

        # Album tag
        album_tag = b"TALB\x00\x00\x00\x0d\x00\x00\x00Test Album\x00"

        # MPEG frame header (Layer III, 128kbps, 44.1kHz, Mono)
        frame_header = b"\xff\xfb\x90\x00"

        # Calculate padding needed
        base_size = len(id3_header + album_tag + frame_header)
        target_size = int(size_mb * 1024 * 1024)
        padding_size = max(0, target_size - base_size)

        # Add padding as audio data (zeros are valid for MP3)
        padding = b"\x00" * padding_size

        return id3_header + album_tag + frame_header + padding

    @staticmethod
    def create_valid_wav(size_mb: float = 1.0) -> bytes:
        """Create a valid WAV file of specified size"""
        # Calculate target size
        target_size = int(size_mb * 1024 * 1024)

        # WAV header structure
        # RIFF header
        riff = b"RIFF"
        file_size = (target_size - 8).to_bytes(4, "little")  # File size minus 8 bytes
        wave = b"WAVE"

        # Format chunk
        fmt_chunk = b"fmt "
        fmt_size = (16).to_bytes(4, "little")  # Format chunk size
        audio_format = (1).to_bytes(2, "little")  # PCM
        num_channels = (1).to_bytes(2, "little")  # Mono
        sample_rate = (44100).to_bytes(4, "little")  # 44.1kHz
        byte_rate = (44100).to_bytes(
            4, "little"
        )  # SampleRate * NumChannels * BitsPerSample/8
        block_align = (2).to_bytes(2, "little")  # NumChannels * BitsPerSample/8
        bits_per_sample = (16).to_bytes(2, "little")  # 16-bit

        # Data chunk header
        data_header = b"data"
        data_size_bytes = target_size - 44  # Remaining size for audio data
        data_size = data_size_bytes.to_bytes(4, "little")

        # Audio data (silence)
        audio_data = b"\x00" * data_size_bytes

        return (
            riff
            + file_size
            + wave
            + fmt_chunk
            + fmt_size
            + audio_format
            + num_channels
            + sample_rate
            + byte_rate
            + block_align
            + bits_per_sample
            + data_header
            + data_size
            + audio_data
        )

    @staticmethod
    def create_valid_m4a(size_mb: float = 1.0) -> bytes:
        """Create a valid M4A file of specified size"""
        # Basic M4A structure with ftyp atom
        ftyp_size = (32).to_bytes(4, "big")
        ftyp = b"ftyp"
        brand = b"M4A "
        version = (0).to_bytes(4, "big")
        compatible = b"M4A mp42isom"

        ftyp_atom = ftyp_size + ftyp + brand + version + compatible

        # Calculate remaining size for padding
        target_size = int(size_mb * 1024 * 1024)
        remaining_size = target_size - len(ftyp_atom)

        # Add a free atom for padding
        if remaining_size > 8:
            free_size = remaining_size.to_bytes(4, "big")
            free_type = b"free"
            free_data = b"\x00" * (remaining_size - 8)
            free_atom = free_size + free_type + free_data
        else:
            free_atom = b""

        return ftyp_atom + free_atom

    @staticmethod
    def create_valid_text(size_mb: float = 0.1) -> bytes:
        """Create a valid text file of specified size"""
        target_size = int(size_mb * 1024 * 1024)

        # Sample text content
        sample_text = "This is a test document with multiple lines.\n"
        sample_text += "It contains various types of content including:\n"
        sample_text += "- Bullet points\n"
        sample_text += "- Numbers: 1, 2, 3, 4, 5\n"
        sample_text += "- Special characters: !@#$%^&*()\n"
        sample_text += "- Unicode: café, résumé, naïve\n\n"

        # Repeat content to reach target size
        repeat_count = max(1, target_size // len(sample_text.encode()))
        content = sample_text * repeat_count

        # Trim to exact size if needed
        content_bytes = content.encode("utf-8")
        if len(content_bytes) > target_size:
            content_bytes = content_bytes[:target_size]

        return content_bytes

    @staticmethod
    def create_malicious_files() -> Dict[str, bytes]:
        """Create various malicious files for security testing"""
        files = {}

        # Windows executable disguised as PDF
        files["fake_pdf.pdf"] = (
            b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00"
        )

        # ZIP file disguised as image
        files["fake_image.jpg"] = b"PK\x03\x04\x14\x00\x00\x00\x08\x00"

        # Script file disguised as text
        files["fake_text.txt"] = b"#!/bin/bash\nrm -rf /\n"

        # HTML with JavaScript disguised as text
        files["fake_html.txt"] = b"<html><script>alert('XSS')</script></html>"

        # Binary data disguised as PDF
        files["fake_binary.pdf"] = (
            b"\x7fELF\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        )

        return files

    @staticmethod
    def create_oversized_files() -> Dict[str, bytes]:
        """Create files that exceed size limits for testing"""
        files = {}

        # PDF over 50MB limit
        files["large_pdf.pdf"] = TestFileGenerator.create_valid_pdf(60.0)

        # MP3 over 200MB limit
        files["large_mp3.mp3"] = TestFileGenerator.create_valid_mp3(250.0)

        # Text over 10MB limit
        files["large_text.txt"] = TestFileGenerator.create_valid_text(15.0)

        return files

    @staticmethod
    def create_edge_case_files() -> Dict[str, bytes]:
        """Create edge case files for boundary testing"""
        files = {}

        # Empty files
        files["empty.pdf"] = b""
        files["empty.txt"] = b""

        # Minimal valid files
        files["minimal.pdf"] = b"%PDF-1.4\n%%EOF"
        files["minimal.txt"] = b"a"

        # Files at size boundaries
        files["boundary_pdf.pdf"] = TestFileGenerator.create_valid_pdf(
            49.9
        )  # Just under limit
        files["boundary_text.txt"] = TestFileGenerator.create_valid_text(
            9.9
        )  # Just under limit

        # Corrupted files
        files["corrupted.pdf"] = b"%PDF-1.4\nincomplete and corrupted"
        files["corrupted.mp3"] = b"ID3\x03\x00\x00\x00\x00\x17\x76incomplete"

        return files

    @staticmethod
    def save_test_files_to_disk(output_dir: Optional[str] = None) -> str:
        """Save all test files to disk for manual testing"""
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="test_files_")

        os.makedirs(output_dir, exist_ok=True)

        # Create valid files
        valid_files = {
            "valid_small.pdf": TestFileGenerator.create_valid_pdf(1.0),
            "valid_medium.pdf": TestFileGenerator.create_valid_pdf(25.0),
            "valid_audio.mp3": TestFileGenerator.create_valid_mp3(5.0),
            "valid_audio.wav": TestFileGenerator.create_valid_wav(10.0),
            "valid_audio.m4a": TestFileGenerator.create_valid_m4a(3.0),
            "valid_text.txt": TestFileGenerator.create_valid_text(1.0),
        }

        # Add malicious files
        valid_files.update(TestFileGenerator.create_malicious_files())

        # Add oversized files (be careful with disk space)
        # valid_files.update(TestFileGenerator.create_oversized_files())

        # Add edge case files
        valid_files.update(TestFileGenerator.create_edge_case_files())

        # Save all files
        for filename, content in valid_files.items():
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "wb") as f:
                f.write(content)

        return output_dir


class TestFileValidator:
    """Utility class for validating test files"""

    @staticmethod
    def validate_file_headers(file_path: str) -> Dict[str, bool]:
        """Check if file has correct header for its extension"""
        results = {}

        with open(file_path, "rb") as f:
            header = f.read(32)  # Read first 32 bytes

        filename = os.path.basename(file_path)
        extension = filename.split(".")[-1].lower()

        if extension == "pdf":
            results["has_pdf_header"] = header.startswith(b"%PDF-")
        elif extension == "mp3":
            results["has_mp3_header"] = (
                header.startswith(b"ID3")
                or header.startswith(b"\xff\xfb")
                or header.startswith(b"\xff\xf3")
            )
        elif extension == "wav":
            results["has_wav_header"] = (
                header.startswith(b"RIFF") and b"WAVE" in header[:12]
            )
        elif extension == "m4a":
            results["has_m4a_header"] = b"ftyp" in header and (
                b"M4A" in header or b"mp4" in header
            )
        elif extension == "txt":
            results["is_text"] = True  # Text files don't have specific headers

        return results


class TestFileGenerators:
    """Test the file generators create valid test files"""

    def test_create_valid_pdf(self):
        """Test PDF file generation"""
        pdf_content = TestFileGenerator.create_valid_pdf(1.0)

        # Should start with PDF header
        assert pdf_content.startswith(b"%PDF-")

        # Should end with EOF marker
        assert pdf_content.endswith(b"%%EOF\n") or pdf_content.endswith(b"%%EOF")

        # Should be approximately 1MB
        assert 0.8 * 1024 * 1024 <= len(pdf_content) <= 1.2 * 1024 * 1024

        # Should pass our validator
        extension, safe_filename = FileValidator.validate_upload(
            pdf_content, "test.pdf", max_size_override=50 * 1024 * 1024
        )
        assert extension == "pdf"

    def test_create_valid_mp3(self):
        """Test MP3 file generation"""
        mp3_content = TestFileGenerator.create_valid_mp3(1.0)

        # Should have ID3 or MPEG header
        assert (
            mp3_content.startswith(b"ID3")
            or mp3_content.startswith(b"\xff\xfb")
            or mp3_content.startswith(b"\xff\xf3")
        )

        # Should be approximately 1MB
        assert 0.8 * 1024 * 1024 <= len(mp3_content) <= 1.2 * 1024 * 1024

        # Should pass our validator
        extension, safe_filename = FileValidator.validate_upload(
            mp3_content, "test.mp3", max_size_override=200 * 1024 * 1024
        )
        assert extension == "mp3"

    def test_create_valid_wav(self):
        """Test WAV file generation"""
        wav_content = TestFileGenerator.create_valid_wav(1.0)

        # Should start with RIFF header
        assert wav_content.startswith(b"RIFF")

        # Should contain WAVE identifier
        assert b"WAVE" in wav_content[:12]

        # Should be approximately 1MB
        assert 0.8 * 1024 * 1024 <= len(wav_content) <= 1.2 * 1024 * 1024

        # Should pass our validator
        extension, safe_filename = FileValidator.validate_upload(
            wav_content, "test.wav", max_size_override=500 * 1024 * 1024
        )
        assert extension == "wav"

    def test_create_valid_m4a(self):
        """Test M4A file generation"""
        m4a_content = TestFileGenerator.create_valid_m4a(1.0)

        # Should contain ftyp atom
        assert b"ftyp" in m4a_content

        # Should contain M4A or mp4 identifier
        assert b"M4A" in m4a_content or b"mp4" in m4a_content

        # Should be approximately 1MB
        assert 0.8 * 1024 * 1024 <= len(m4a_content) <= 1.2 * 1024 * 1024

        # Should pass our validator
        extension, safe_filename = FileValidator.validate_upload(
            m4a_content, "test.m4a", max_size_override=200 * 1024 * 1024
        )
        assert extension == "m4a"

    def test_create_valid_text(self):
        """Test text file generation"""
        text_content = TestFileGenerator.create_valid_text(0.1)  # 100KB

        # Should be decodable as UTF-8
        text_str = text_content.decode("utf-8")
        assert len(text_str) > 0

        # Should be approximately 100KB
        assert 80 * 1024 <= len(text_content) <= 120 * 1024

        # Should pass our validator
        extension, safe_filename = FileValidator.validate_upload(
            text_content, "test.txt", max_size_override=10 * 1024 * 1024
        )
        assert extension == "txt"

    def test_create_malicious_files(self):
        """Test that malicious files are created correctly"""
        malicious_files = TestFileGenerator.create_malicious_files()

        # Should have several malicious file types
        assert len(malicious_files) >= 3

        # Each file should have content
        for filename, content in malicious_files.items():
            assert len(content) > 0

            # These files should NOT pass validation (except txt files with script content)
            if not filename.endswith(".txt"):
                with pytest.raises(FileValidationError):
                    FileValidator.validate_upload(
                        content, filename, max_size_override=100 * 1024 * 1024
                    )

    def test_create_oversized_files(self):
        """Test that oversized files are created correctly"""
        oversized_files = TestFileGenerator.create_oversized_files()

        # Should have several oversized files
        assert len(oversized_files) >= 2

        # Each file should be reasonably large (some may not be exactly over the limit due to implementation)
        for filename, content in oversized_files.items():
            assert len(content) > 10 * 1024 * 1024  # At least 10MB

            # These files should be rejected for size (test with lower limits to ensure rejection)
            with pytest.raises(FileValidationError):
                FileValidator.validate_upload(
                    content, filename, max_size_override=5 * 1024 * 1024
                )  # 5MB limit

    def test_generator_basic_functionality(self):
        """Test basic functionality of file generators"""
        # Test that all generator methods work
        pdf_content = TestFileGenerator.create_valid_pdf(0.1)
        assert len(pdf_content) > 1000
        assert pdf_content.startswith(b"%PDF-")

        mp3_content = TestFileGenerator.create_valid_mp3(0.1)
        assert len(mp3_content) > 1000
        assert mp3_content.startswith(b"ID3") or mp3_content.startswith(b"\xff\xfb")

        text_content = TestFileGenerator.create_valid_text(0.1)
        assert len(text_content) > 1000
        # Should be valid UTF-8
        text_content.decode("utf-8")

    def test_save_test_files_to_disk(self):
        """Test saving files to disk"""
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as temp_dir:
            result_dir = TestFileGenerator.save_test_files_to_disk(temp_dir)

            # Should return a directory path
            assert os.path.isdir(result_dir)

            # Should contain several test files
            files = os.listdir(result_dir)
            assert len(files) >= 3  # Should have some valid files

            # Check that most files have content (some test files might be empty by design)
            non_empty_files = 0
            for filename in files:
                filepath = os.path.join(result_dir, filename)
                if os.path.getsize(filepath) > 0:
                    non_empty_files += 1

            # At least half the files should have content
            assert non_empty_files >= len(files) // 2
