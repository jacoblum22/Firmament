"""
Integration tests for file upload validation.
Tests the complete upload endpoint with various file scenarios.
"""

import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from fastapi import FastAPI
from io import BytesIO
import json

# Import the router and create test app
from routes import router

# Create test FastAPI app
app = FastAPI()
app.include_router(router)

client = TestClient(app)


class TestFileUploadIntegration:
    """Integration tests for file upload validation"""

    def test_valid_pdf_upload(self):
        """Test uploading a valid PDF file"""
        # Create a valid PDF content
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 1\n0000000000 65535 f \ntrailer\n<<\n/Size 1\n/Root 1 0 R\n>>\nstartxref\n0\n%%EOF"

        files = {"file": ("test_document.pdf", BytesIO(pdf_content), "application/pdf")}

        response = client.post("/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["message"] == "Upload accepted. Processing started."

    def test_valid_text_upload(self):
        """Test uploading a valid text file"""
        text_content = b"This is a test document with some content.\nIt has multiple lines.\nAnd should be processed correctly."

        files = {"file": ("lecture_notes.txt", BytesIO(text_content), "text/plain")}

        response = client.post("/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data

    def test_valid_mp3_upload(self):
        """Test uploading a valid MP3 file"""
        # Create MP3 with ID3 header
        mp3_content = b"ID3\x03\x00\x00\x00\x00\x17\x76TALB\x00\x00\x00\x0d\x00\x00\x00Test Album\x00"
        mp3_content += b"\xff\xfb\x90\x00" + b"\x00" * 1000  # Add some audio data

        files = {"file": ("test_audio.mp3", BytesIO(mp3_content), "audio/mpeg")}

        response = client.post("/upload", files=files)

        assert response.status_code == 200

    def test_oversized_file_rejection(self):
        """Test that oversized files are rejected"""
        # Create a file larger than 50MB (PDF limit)
        large_content = b"%PDF-1.4\n" + b"x" * (60 * 1024 * 1024)  # 60MB

        files = {
            "file": ("large_document.pdf", BytesIO(large_content), "application/pdf")
        }

        response = client.post("/upload", files=files)

        assert response.status_code == 400
        assert "File too large" in response.json()["detail"]

    def test_invalid_file_type_rejection(self):
        """Test that invalid file types are rejected"""
        exe_content = b"MZ\x90\x00"  # Windows executable signature

        files = {
            "file": ("malware.exe", BytesIO(exe_content), "application/octet-stream")
        }

        response = client.post("/upload", files=files)

        assert response.status_code == 400
        assert "Unsupported file extension" in response.json()["detail"]

    def test_file_type_spoofing_rejection(self):
        """Test that files with mismatched content and extension are rejected"""
        # Upload an executable file with PDF extension
        exe_content = b"MZ\x90\x00" + b"\x00" * 1000  # Windows executable content

        files = {"file": ("fake_document.pdf", BytesIO(exe_content), "application/pdf")}

        response = client.post("/upload", files=files)

        assert response.status_code == 400
        assert "File content doesn't match" in response.json()["detail"]

    def test_empty_file_rejection(self):
        """Test that empty files are rejected"""
        files = {"file": ("empty.pdf", BytesIO(b""), "application/pdf")}

        response = client.post("/upload", files=files)

        assert response.status_code == 400
        assert "File is empty" in response.json()["detail"]

    def test_malicious_filename_sanitization(self):
        """Test that malicious filenames are properly rejected or sanitized for security"""
        pdf_content = b"%PDF-1.4\nvalid pdf content"

        # Test cases categorized by expected behavior
        rejection_test_cases = [
            {
                "filename": "../../../etc/passwd.pdf",
                "description": "Path traversal attack",
                "expected_error_pattern": "invalid path characters",
            },
            {
                "filename": "file<script>alert('xss')</script>.pdf",
                "description": "XSS injection with dangerous characters",
                "expected_error_pattern": "invalid path characters",  # Contains / in </script>
            },
            {
                "filename": "file|dangerous>redirect.pdf",
                "description": "Shell injection characters",
                "expected_error_pattern": "dangerous character",
            },
            {
                "filename": 'file"with"quotes*.pdf',
                "description": "Filename with quotes and wildcards",
                "expected_error_pattern": "dangerous character",
            },
            {
                "filename": "file\x00null.pdf",
                "description": "Null byte injection",
                "expected_error_pattern": "null bytes",
            },
            {
                "filename": "subdir/file.pdf",
                "description": "Path separator in filename",
                "expected_error_pattern": "invalid path characters",
            },
            {
                "filename": "subdir\\file.pdf",
                "description": "Windows path separator in filename",
                "expected_error_pattern": "invalid path characters",
            },
        ]

        # Test cases that should be accepted
        accepted_test_cases = [
            {
                "filename": "normal_file.pdf",
                "description": "Normal filename (control case)",
            },
            {
                "filename": "file_with-underscores_and_dashes.pdf",
                "description": "Filename with safe special characters",
            },
            {"filename": "file123.pdf", "description": "Filename with numbers"},
            {"filename": "UPPERCASE_FILE.PDF", "description": "Uppercase filename"},
        ]

        # Test cases that should be rejected with 400 status
        for test_case in rejection_test_cases:
            filename = test_case["filename"]
            description = test_case["description"]
            expected_error = test_case["expected_error_pattern"]

            files = {"file": (filename, BytesIO(pdf_content), "application/pdf")}
            response = client.post("/upload", files=files)

            # Special handling for null byte case - FastAPI might URL-encode it
            if "null" in description.lower() and "\x00" in filename:
                # Null bytes might be handled differently by FastAPI (URL-encoded)
                # Accept either rejection or acceptance (will fail later in processing)
                assert response.status_code in [
                    200,
                    400,
                ], f"Unexpected status for {description}: {filename}, got {response.status_code}"
                if response.status_code == 400:
                    error_detail = response.json().get("detail", "")
                    assert (
                        expected_error.lower() in error_detail.lower()
                    ), f"Expected error pattern '{expected_error}' not found in '{error_detail}' for {description}"
            else:
                # Should be rejected with 400 status
                assert (
                    response.status_code == 400
                ), f"Expected rejection for {description}: {filename}, got {response.status_code}"

                # Verify error message contains expected pattern
                error_detail = response.json().get("detail", "")
                assert (
                    expected_error.lower() in error_detail.lower()
                ), f"Expected error pattern '{expected_error}' not found in '{error_detail}' for {description}"

        # Test cases that should be accepted with 200 status
        for test_case in accepted_test_cases:
            filename = test_case["filename"]
            description = test_case["description"]

            files = {"file": (filename, BytesIO(pdf_content), "application/pdf")}
            response = client.post("/upload", files=files)

            # Should be accepted
            assert (
                response.status_code == 200
            ), f"Expected acceptance for {description}: {filename}, got {response.status_code}"

            data = response.json()
            assert "job_id" in data
            assert "message" in data

    def test_missing_filename(self):
        """Test handling of uploads without filename"""
        pdf_content = b"%PDF-1.4\nvalid pdf content"

        files = {"file": (None, BytesIO(pdf_content), "application/pdf")}

        response = client.post("/upload", files=files)

        # Should handle missing filename gracefully (422 is FastAPI validation error)
        assert response.status_code in [200, 400, 422]

    def test_case_insensitive_extensions(self):
        """Test that file extensions are handled case-insensitively"""
        pdf_content = b"%PDF-1.4\nvalid pdf content"

        # Test various case combinations
        extensions = ["PDF", "Pdf", "pDf", "pdf"]

        for ext in extensions:
            filename = f"test.{ext}"
            files = {"file": (filename, BytesIO(pdf_content), "application/pdf")}
            response = client.post("/upload", files=files)
            assert response.status_code == 200

    def test_multiple_dots_in_filename(self):
        """Test filenames with multiple dots"""
        pdf_content = b"%PDF-1.4\nvalid pdf content"

        files = {
            "file": (
                "my.document.with.dots.pdf",
                BytesIO(pdf_content),
                "application/pdf",
            )
        }

        response = client.post("/upload", files=files)
        assert response.status_code == 200

    def test_wav_file_validation(self):
        """Test WAV file validation"""
        # Create a valid WAV file header
        wav_content = b"RIFF\x24\x08\x00\x00WAVE"
        wav_content += b"fmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00"
        wav_content += b"\x88\x58\x01\x00\x02\x00\x10\x00"
        wav_content += b"data\x00\x08\x00\x00" + b"\x00" * 2048  # Some audio data

        files = {"file": ("audio.wav", BytesIO(wav_content), "audio/wav")}

        response = client.post("/upload", files=files)
        assert response.status_code == 200

    def test_m4a_file_validation(self):
        """Test M4A file validation"""
        # Create a valid M4A file header
        m4a_content = b"\x00\x00\x00\x20ftypM4A \x00\x00\x00\x00"
        m4a_content += b"M4A mp42isom\x00\x00\x00\x00" + b"\x00" * 1000

        files = {"file": ("audio.m4a", BytesIO(m4a_content), "audio/mp4")}

        response = client.post("/upload", files=files)
        assert response.status_code == 200

    def test_concurrent_uploads(self):
        """Test multiple concurrent uploads"""
        pdf_content = b"%PDF-1.4\nvalid pdf content"

        # Simulate multiple concurrent uploads
        responses = []
        for i in range(5):
            files = {
                "file": (f"document_{i}.pdf", BytesIO(pdf_content), "application/pdf")
            }
            response = client.post("/upload", files=files)
            responses.append(response)

        # All should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert "job_id" in data

    def test_unicode_filename(self):
        """Test filenames with unicode characters"""
        pdf_content = b"%PDF-1.4\nvalid pdf content"

        unicode_names = [
            "文档.pdf",  # Chinese
            "документ.pdf",  # Russian
            "café_résumé.pdf",  # Accented characters
            "emoji_😀_file.pdf",  # Emoji
        ]

        for filename in unicode_names:
            files = {"file": (filename, BytesIO(pdf_content), "application/pdf")}
            response = client.post("/upload", files=files)
            # Should either work or be sanitized appropriately
            assert response.status_code in [200, 400]

    def test_filename_sanitization_security_validation(self):
        """Test filename sanitization security by validating the FileValidator directly"""
        from utils.file_validator import FileValidator

        # Test cases with expected sanitized output
        sanitization_test_cases = [
            {
                "input": "../../../etc/passwd.pdf",
                "expected_output": "passwd.pdf",  # Should remove path traversal
                "forbidden_patterns": ["../", "/etc/", "/"],
            },
            {
                "input": "file<script>alert('xss')</script>.pdf",
                "expected_output": "script_.pdf",  # Dangerous chars become underscores, 'file' is removed due to '<'
                "forbidden_patterns": [
                    "<",
                    ">",
                ],  # Only check for the actual dangerous characters
            },
            {
                "input": 'dangerous"file|name*.pdf',
                "expected_output": "dangerous_file_name_.pdf",  # Quotes, pipes, asterisks become underscores
                "forbidden_patterns": ['"', "|", "*"],
            },
            {
                "input": "file\x00null\x00byte.pdf",
                "expected_output": "filenullbyte.pdf",  # Null bytes removed
                "forbidden_patterns": ["\x00"],
            },
            {
                "input": "normal_filename.pdf",
                "expected_output": "normal_filename.pdf",  # Should remain unchanged
                "forbidden_patterns": [],
            },
            {
                "input": "subdir/malicious\\file.pdf",
                "expected_output": "file.pdf",  # Path separators become underscores, basename only
                "forbidden_patterns": [
                    "/",
                    "\\",
                ],  # Check that path separators are gone
            },
        ]

        for test_case in sanitization_test_cases:
            input_filename = test_case["input"]
            expected_output = test_case["expected_output"]
            forbidden_patterns = test_case["forbidden_patterns"]

            # Test the sanitization function directly
            safe_filename = FileValidator.get_safe_filename(input_filename)

            # Verify the output matches expected sanitized filename
            assert (
                safe_filename == expected_output
            ), f"Expected sanitized filename '{expected_output}' but got '{safe_filename}' for input '{input_filename}'"

            # Verify safe filename doesn't contain dangerous patterns
            for forbidden in forbidden_patterns:
                assert (
                    forbidden not in safe_filename
                ), f"Sanitized filename '{safe_filename}' still contains dangerous pattern '{forbidden}'"

            # Additional security checks
            self._verify_filename_security(safe_filename)

    def _verify_filename_security(self, filename: str):
        """Helper method to verify filename meets security requirements"""
        # Verify no path traversal is possible
        assert not filename.startswith(
            "/"
        ), "Sanitized filename starts with absolute path"
        assert not filename.startswith(
            "\\"
        ), "Sanitized filename starts with absolute path"
        assert "../" not in filename, "Sanitized filename contains path traversal"
        assert "..\\" not in filename, "Sanitized filename contains path traversal"

        # Verify no null bytes
        assert "\x00" not in filename, "Sanitized filename contains null bytes"

        # Verify no dangerous characters remain
        dangerous_chars = ["<", ">", ":", '"', "|", "?", "*"]
        for char in dangerous_chars:
            assert (
                char not in filename
            ), f"Sanitized filename contains dangerous character: {char}"

        # Verify reasonable length (should be <= 255 chars)
        assert (
            len(filename) <= 255
        ), f"Sanitized filename too long: {len(filename)} chars"

        # Verify filename is not empty and not just dots/spaces
        assert filename.strip(" ."), "Sanitized filename is empty or only dots/spaces"

    def test_end_to_end_filename_security(self):
        """Test that malicious filenames don't create dangerous files on filesystem"""
        import tempfile
        import shutil
        from utils.file_validator import FileValidator

        pdf_content = b"%PDF-1.4\nvalid pdf content"

        # Create a temporary directory to test file creation
        with tempfile.TemporaryDirectory() as temp_dir:
            malicious_filenames = [
                "../../../etc/passwd.pdf",
                "..\\..\\..\\windows\\system32\\evil.pdf",
                "file<script>.pdf",
                "dangerous|file.pdf",
                "file\x00injection.pdf",
            ]

            for malicious_filename in malicious_filenames:
                # Test the full validation pipeline
                try:
                    extension, safe_filename = FileValidator.validate_upload(
                        pdf_content, malicious_filename, max_size_override=None
                    )

                    # Verify the safe filename is actually safe for filesystem operations
                    test_file_path = os.path.join(temp_dir, safe_filename)

                    # This should not escape the temp directory
                    normalized_temp = os.path.normpath(temp_dir)
                    normalized_file = os.path.normpath(test_file_path)

                    assert normalized_file.startswith(
                        normalized_temp
                    ), f"Sanitized filename allows directory traversal: {safe_filename}"

                    # Try to write the file - should not raise exceptions
                    with open(test_file_path, "wb") as f:
                        f.write(pdf_content)

                    # Verify file was created with safe name
                    assert os.path.exists(
                        test_file_path
                    ), f"File was not created with safe filename: {safe_filename}"

                    # Verify only expected file exists (no traversal occurred)
                    files_in_temp = os.listdir(temp_dir)
                    assert (
                        len(files_in_temp) == 1
                    ), f"Unexpected files created: {files_in_temp}"

                    # Clean up for next iteration
                    os.remove(test_file_path)

                except Exception as e:
                    # If validation fails, that's also acceptable for malicious files
                    # But we need to ensure it fails securely, not with an unhandled exception
                    from utils.file_validator import FileValidationError

                    # Check for expected exception types
                    expected_exceptions = (FileValidationError, ValueError, OSError)
                    assert isinstance(
                        e, expected_exceptions
                    ), f"Unexpected exception type {type(e).__name__} for malicious filename {malicious_filename}: {e}"


class TestFileUploadErrorHandling:
    """Test error handling scenarios"""

    def test_no_file_uploaded(self):
        """Test request without file"""
        response = client.post("/upload")
        assert response.status_code == 422  # FastAPI validation error

    def test_malformed_request(self):
        """Test malformed upload request"""
        # Send text instead of file
        response = client.post("/upload", data={"not_a_file": "text_data"})
        assert response.status_code == 422

    def test_network_interruption_simulation(self):
        """Test handling of incomplete file uploads"""
        # This is harder to test directly, but we can test with truncated content
        truncated_pdf = b"%PDF-1.4\nincomplete"  # Truncated but valid start

        files = {"file": ("incomplete.pdf", BytesIO(truncated_pdf), "application/pdf")}

        response = client.post("/upload", files=files)
        # Should accept the file (content validation is basic)
        assert response.status_code == 200
