"""
Comprehensive test suite for file upload validation.
This includes both unit tests and integration tests.
"""

import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from fastapi import FastAPI
from io import BytesIO
import time

# Import test utilities
from tests.utils.test_file_generators import TestFileGenerator, TestFileValidator

# Import the components to test
from utils.file_validator import FileValidator, FileValidationError
from routes import router

# Create test FastAPI app
app = FastAPI()
app.include_router(router)
client = TestClient(app)


@pytest.fixture
def test_files():
    """Fixture to create test files for the session"""
    temp_dir = tempfile.mkdtemp(prefix="upload_test_")

    # Generate test files
    test_dir = TestFileGenerator.save_test_files_to_disk(temp_dir)

    yield test_dir

    # Cleanup after tests
    import shutil

    try:
        shutil.rmtree(temp_dir)
    except Exception:
        pass  # Best effort cleanup


class TestFileUploadValidationSuite:
    """Comprehensive test suite for file upload validation"""

    def test_file_generator_creates_valid_files(self, test_files):
        """Test that our file generators create valid files"""

        # Test PDF generation
        pdf_content = TestFileGenerator.create_valid_pdf(1.0)
        assert pdf_content.startswith(b"%PDF-")
        assert pdf_content.endswith(b"%%EOF\n")
        assert len(pdf_content) > 1024 * 1024  # At least 1MB

        # Test MP3 generation
        mp3_content = TestFileGenerator.create_valid_mp3(1.0)
        assert mp3_content.startswith(b"ID3") or b"\xff\xfb" in mp3_content[:10]

        # Test WAV generation
        wav_content = TestFileGenerator.create_valid_wav(1.0)
        assert wav_content.startswith(b"RIFF")
        assert b"WAVE" in wav_content[:12]

        # Test text generation
        text_content = TestFileGenerator.create_valid_text(0.1)
        assert len(text_content) > 0
        # Should be valid UTF-8
        text_content.decode("utf-8")

    def test_unit_validation_valid_files(self):
        """Test FileValidator with valid files"""

        # Test valid PDF
        pdf_content = TestFileGenerator.create_valid_pdf(1.0)
        ext, safe_name = FileValidator.validate_upload(pdf_content, "test.pdf")
        assert ext == "pdf"
        assert safe_name == "test.pdf"

        # Test valid MP3
        mp3_content = TestFileGenerator.create_valid_mp3(1.0)
        ext, safe_name = FileValidator.validate_upload(mp3_content, "audio.mp3")
        assert ext == "mp3"
        assert safe_name == "audio.mp3"

        # Test valid text
        text_content = TestFileGenerator.create_valid_text(0.1)
        ext, safe_name = FileValidator.validate_upload(text_content, "document.txt")
        assert ext == "txt"
        assert safe_name == "document.txt"

    def test_unit_validation_malicious_files(self):
        """Test FileValidator rejects malicious files"""

        malicious_files = TestFileGenerator.create_malicious_files()

        for filename, content in malicious_files.items():
            # Text files with script content should still pass validation at the file level
            # (content filtering would happen at a different layer)
            if filename.endswith(".txt"):
                # These should pass basic validation but may be flagged later
                try:
                    ext, safe_name = FileValidator.validate_upload(content, filename)
                    assert ext == "txt"
                except FileValidationError:
                    # It's also acceptable if they're rejected
                    pass
            else:
                # Non-text files with wrong signatures should be rejected
                with pytest.raises(FileValidationError):
                    FileValidator.validate_upload(content, filename)

    def test_unit_validation_oversized_files(self):
        """Test FileValidator rejects oversized files"""

        # Create a file that's too large for its type
        large_pdf = TestFileGenerator.create_valid_pdf(60.0)  # Over 50MB limit

        with pytest.raises(FileValidationError, match="File too large"):
            FileValidator.validate_upload(large_pdf, "large.pdf")

    def test_integration_valid_uploads(self):
        """Test complete upload flow with valid files"""

        # Test valid PDF upload
        pdf_content = TestFileGenerator.create_valid_pdf(1.0)
        files = {"file": ("document.pdf", BytesIO(pdf_content), "application/pdf")}
        response = client.post("/upload", files=files)
        assert response.status_code == 200
        assert "job_id" in response.json()

        # Test valid audio upload
        mp3_content = TestFileGenerator.create_valid_mp3(5.0)
        files = {"file": ("audio.mp3", BytesIO(mp3_content), "audio/mpeg")}
        response = client.post("/upload", files=files)
        assert response.status_code == 200

    def test_integration_malicious_uploads(self):
        """Test that malicious uploads are rejected"""

        malicious_files = TestFileGenerator.create_malicious_files()

        for filename, content in malicious_files.items():
            files = {"file": (filename, BytesIO(content), "application/octet-stream")}
            response = client.post("/upload", files=files)

            # Text files might be accepted but other malicious files should be rejected
            if filename.endswith(".txt"):
                # Text files might pass basic validation
                assert response.status_code in [200, 400]
            else:
                # Non-text malicious files should be rejected
                assert response.status_code == 400
                detail = response.json()["detail"].lower()
                # Should contain some indication of error/rejection
                assert any(
                    word in detail
                    for word in ["error", "unsupported", "invalid", "match", "format"]
                )

    def test_integration_oversized_uploads(self):
        """Test that oversized uploads are rejected"""

        # Create oversized PDF
        large_pdf = TestFileGenerator.create_valid_pdf(60.0)
        files = {"file": ("large.pdf", BytesIO(large_pdf), "application/pdf")}
        response = client.post("/upload", files=files)
        assert response.status_code == 400
        assert "too large" in response.json()["detail"].lower()

    def test_security_filename_sanitization(self):
        """Test that dangerous filenames are handled properly"""

        pdf_content = TestFileGenerator.create_valid_pdf(0.1)

        dangerous_filenames = [
            "../../../etc/passwd.pdf",
            "file<script>.pdf",
            "file|pipe.pdf",
            "file:colon.pdf",
            "file*wildcard.pdf",
            "file\x00null.pdf",
        ]

        for dangerous_name in dangerous_filenames:
            try:
                # Test unit validation
                ext, safe_name = FileValidator.validate_upload(
                    pdf_content, dangerous_name
                )
                # If it passes, the filename should be sanitized
                assert "../" not in safe_name
                assert "<" not in safe_name
                assert "|" not in safe_name
                assert "\x00" not in safe_name

                # Test integration
                files = {
                    "file": (dangerous_name, BytesIO(pdf_content), "application/pdf")
                }
                response = client.post("/upload", files=files)
                # Should either be rejected or accepted with sanitized name
                assert response.status_code in [200, 400]

            except FileValidationError:
                # It's also acceptable to reject dangerous filenames outright
                pass

    def test_performance_large_valid_files(self):
        """Test performance with large but valid files"""

        # Test with a large but acceptable file
        large_pdf = TestFileGenerator.create_valid_pdf(45.0)  # Just under 50MB limit

        start_time = time.time()

        # Test validation performance
        ext, safe_name = FileValidator.validate_upload(large_pdf, "large_doc.pdf")

        validation_time = time.time() - start_time

        # Validation should complete within reasonable time (adjust threshold as needed)
        assert validation_time < 5.0  # Should take less than 5 seconds
        assert ext == "pdf"

    def test_edge_cases(self):
        """Test various edge cases"""

        edge_files = TestFileGenerator.create_edge_case_files()

        for filename, content in edge_files.items():
            if "empty" in filename:
                # Empty files should be rejected
                with pytest.raises(FileValidationError, match="empty"):
                    FileValidator.validate_upload(content, filename)

            elif "minimal" in filename:
                # Minimal files should pass
                try:
                    ext, safe_name = FileValidator.validate_upload(content, filename)
                    assert ext in ["pdf", "txt"]
                except FileValidationError:
                    # Some minimal files might still be rejected, which is okay
                    pass

            elif "boundary" in filename:
                # Files at size boundary should pass
                ext, safe_name = FileValidator.validate_upload(content, filename)
                assert ext in ["pdf", "txt"]

            elif "corrupted" in filename:
                # Corrupted files might be rejected depending on validation strictness
                try:
                    FileValidator.validate_upload(content, filename)
                except FileValidationError:
                    pass  # Rejection of corrupted files is acceptable

    def test_concurrent_validation(self):
        """Test concurrent validation doesn't cause issues"""

        import threading
        import queue

        results = queue.Queue()

        def validate_file(file_num):
            try:
                pdf_content = TestFileGenerator.create_valid_pdf(1.0)
                ext, safe_name = FileValidator.validate_upload(
                    pdf_content, f"test_{file_num}.pdf"
                )
                results.put(("success", file_num, ext))
            except Exception as e:
                results.put(("error", file_num, str(e)))

        # Start multiple validation threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=validate_file, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Check results
        successes = 0
        while not results.empty():
            status, file_num, result = results.get()
            if status == "success":
                successes += 1
                assert result == "pdf"

        assert successes == 10  # All validations should succeed

    def test_memory_usage_large_files(self):
        """Test that large file validation doesn't consume excessive memory"""

        # Skip this test if psutil is not available
        try:
            import psutil
            import os
        except ImportError:
            pytest.skip("psutil not installed - skipping memory usage test")

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Validate a large file
        large_pdf = TestFileGenerator.create_valid_pdf(40.0)  # 40MB
        ext, safe_name = FileValidator.validate_upload(large_pdf, "large.pdf")

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 2x file size)
        max_acceptable_increase = 2 * 40 * 1024 * 1024  # 80MB
        assert memory_increase < max_acceptable_increase

    def test_unicode_handling(self):
        """Test handling of unicode filenames and content"""

        # Test unicode filenames
        unicode_names = [
            "文档.pdf",  # Chinese
            "документ.pdf",  # Russian
            "café.pdf",  # Accented characters
        ]

        pdf_content = TestFileGenerator.create_valid_pdf(0.1)

        for unicode_name in unicode_names:
            try:
                ext, safe_name = FileValidator.validate_upload(
                    pdf_content, unicode_name
                )
                # Should handle unicode gracefully
                assert ext == "pdf"
                assert len(safe_name) > 0
            except UnicodeError:
                pytest.fail(f"Unicode handling failed for {unicode_name}")

    def test_stress_testing(self):
        """Stress test the validation system"""

        # Test many small files
        for i in range(100):
            pdf_content = TestFileGenerator.create_valid_pdf(0.1)  # Small files
            ext, safe_name = FileValidator.validate_upload(
                pdf_content, f"stress_test_{i}.pdf"
            )
            assert ext == "pdf"

        # Test with various file types
        generators = [
            ("pdf", lambda: TestFileGenerator.create_valid_pdf(0.5)),
            ("mp3", lambda: TestFileGenerator.create_valid_mp3(1.0)),
            ("txt", lambda: TestFileGenerator.create_valid_text(0.1)),
        ]

        for file_type, generator in generators:
            for i in range(20):
                content = generator()
                ext, safe_name = FileValidator.validate_upload(
                    content, f"stress_{file_type}_{i}.{file_type}"
                )
                assert ext == file_type
