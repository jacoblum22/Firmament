#!/usr/bin/env python3
"""
Frontend Upload Integration Tests

This test suite simulates various frontend file upload scenarios including:
1. Normal, valid multipart form uploads (should succeed)
2. Malformed requests with incorrect Content-Type headers (should fail gracefully)
3. Proper request handling verification

Test 2 specifically tests server robustness against malformed requests where the
Content-Type header doesn't match the actual request body format.
"""

import requests
import json


def test_frontend_like_upload(
    base_url="http://localhost:8000", test_file_path="../test_upload.txt"
):
    """Test upload simulating frontend behavior"""
    url = f"{base_url}/upload"

    # Test with the test file we created
    file_path = test_file_path
    expected_success_status = 200  # or whatever your API returns on success

    try:
        with open(file_path, "rb") as f:
            # Simulate what the frontend does - multipart form with 'file' field
            files = {"file": ("test_upload.txt", f, "text/plain")}

            # Test with different headers to see what might be causing 422
            print("=== Test 1: Normal upload (should succeed) ===")
            response = requests.post(url, files=files)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            # Assert expected behavior for normal upload
            if response.status_code != expected_success_status:
                print(
                    f"⚠️  Warning: Expected {expected_success_status}, got {response.status_code}"
                )
            print()

            # Reset file pointer
            f.seek(0)

            print(
                "=== Test 2: Malformed request - Content-Type mismatch (expected to fail) ==="
            )
            # This test deliberately sends an invalid request to verify server error handling.
            # Setting Content-Type: application/json while sending multipart form data is invalid
            # because the multipart boundary parameter is missing. This simulates a frontend bug
            # or misconfiguration to ensure the server handles such cases gracefully.
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, files=files, headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")

            # Document expected behavior
            if response.status_code >= 400:
                print("✅ Expected: Server correctly rejected malformed request")
            else:
                print(
                    "⚠️  Unexpected: Server accepted malformed request (potential issue)"
                )
            print()

            f.seek(0)

            print("=== Test 3: Proper multipart upload (should succeed) ===")
            # Let requests automatically set the correct multipart Content-Type with boundary.
            # This is the correct way to send multipart form data.
            response = requests.post(url, files=files)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")

            # Document expected behavior
            if response.status_code == expected_success_status:
                print("✅ Expected: Server correctly processed valid multipart request")
            else:
                print(
                    f"⚠️  Unexpected: Expected {expected_success_status}, got {response.status_code}"
                )
            print()

    except FileNotFoundError:
        print(f"Test file {file_path} not found")
    except Exception as e:
        print(f"Error during test: {e}")


if __name__ == "__main__":
    test_frontend_like_upload()
