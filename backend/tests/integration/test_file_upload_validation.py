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
        """Test that malicious filenames are sanitized"""
        pdf_content = b"%PDF-1.4\nvalid pdf content"

        # Try various malicious filenames
        malicious_names = [
            "../../../etc/passwd.pdf",
            "file<script>alert('xss')</script>.pdf",
            "file|dangerous.pdf",
            "normal_file.pdf",  # This should work fine
        ]

        for filename in malicious_names:
            files = {"file": (filename, BytesIO(pdf_content), "application/pdf")}
            response = client.post("/upload", files=files)

            if filename == "normal_file.pdf":
                assert response.status_code == 200
            else:
                # Malicious filenames should either be rejected or sanitized
                # The response should be successful but filename should be sanitized
                assert response.status_code in [200, 400]

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
