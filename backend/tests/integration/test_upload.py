#!/usr/bin/env python3

import requests
import os
import json
import pytest
import tempfile


def test_upload_valid_file():
    """Test file upload with a valid PDF file"""
    url = "http://localhost:8000/upload"

    # Create a simple test PDF file
    test_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n174\n%%EOF"

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
        temp_file.write(test_content)
        temp_file_path = temp_file.name

    try:
        with open(temp_file_path, "rb") as f:
            files = {"file": (os.path.basename(temp_file_path), f, "application/pdf")}

            response = requests.post(url, files=files, timeout=30)

            # Test assertions
            assert response.status_code in [
                200,
                201,
            ], f"Expected successful upload, got {response.status_code}: {response.text}"

            # Verify response structure
            if response.headers.get("content-type", "").startswith("application/json"):
                response_data = response.json()
                assert isinstance(
                    response_data, dict
                ), "Response should be a JSON object"
                # Add more specific assertions based on your API response structure

    except requests.exceptions.Timeout:
        pytest.fail("Upload request timed out - check if server is running")
    except requests.exceptions.ConnectionError:
        pytest.skip("Cannot connect to server - ensure it's running on localhost:8000")
    except Exception as e:
        pytest.fail(f"Unexpected error during upload test: {e}")
    finally:
        # Cleanup
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


def test_upload_invalid_file():
    """Test file upload with an invalid file type"""
    url = "http://localhost:8000/upload"

    # Create a test file with invalid content
    with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as temp_file:
        temp_file.write(b"Invalid file content")
        temp_file_path = temp_file.name

    try:
        with open(temp_file_path, "rb") as f:
            files = {
                "file": (
                    os.path.basename(temp_file_path),
                    f,
                    "application/octet-stream",
                )
            }

            response = requests.post(url, files=files, timeout=30)

            # Should reject invalid file types
            assert response.status_code in [
                400,
                422,
            ], f"Expected error for invalid file type, got {response.status_code}"

    except requests.exceptions.Timeout:
        pytest.fail("Upload request timed out - check if server is running")
    except requests.exceptions.ConnectionError:
        pytest.skip("Cannot connect to server - ensure it's running on localhost:8000")
    except Exception as e:
        pytest.fail(f"Unexpected error during invalid file test: {e}")
    finally:
        # Cleanup
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


def test_upload_empty_file():
    """Test file upload with an empty file"""
    url = "http://localhost:8000/upload"

    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
        # File is created but no content written (empty file)
        temp_file_path = temp_file.name

    try:
        with open(temp_file_path, "rb") as f:
            files = {"file": (os.path.basename(temp_file_path), f, "text/plain")}

            response = requests.post(url, files=files, timeout=30)

            # Should handle empty files appropriately
            assert response.status_code in [
                400,
                422,
            ], f"Expected error for empty file, got {response.status_code}"

    except requests.exceptions.Timeout:
        pytest.fail("Upload request timed out - check if server is running")
    except requests.exceptions.ConnectionError:
        pytest.skip("Cannot connect to server - ensure it's running on localhost:8000")
    except Exception as e:
        pytest.fail(f"Unexpected error during empty file test: {e}")
    finally:
        # Cleanup
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


if __name__ == "__main__":
    # Run all tests when executed directly
    test_upload_valid_file()
    test_upload_invalid_file()
    test_upload_empty_file()
    print("✅ All upload tests completed!")
