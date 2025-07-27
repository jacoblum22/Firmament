#!/usr/bin/env python3

import requests
import json


def test_frontend_like_upload():
    """Test upload simulating frontend behavior"""
    url = "http://localhost:8000/upload"

    # Test with the test file we created
    file_path = "../test_upload.txt"

    try:
        with open(file_path, "rb") as f:
            # Simulate what the frontend does - multipart form with 'file' field
            files = {"file": ("test_upload.txt", f, "text/plain")}

            # Test with different headers to see what might be causing 422
            print("=== Test 1: Normal upload ===")
            response = requests.post(url, files=files)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            print()

            # Reset file pointer
            f.seek(0)

            print("=== Test 2: Upload with Content-Type application/json header ===")
            # This might simulate the issue where the frontend accidentally sets Content-Type
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, files=files, headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            print()

            f.seek(0)

            print("=== Test 3: Upload with explicit multipart Content-Type ===")
            # Try with explicit multipart content type
            headers = {"Content-Type": "multipart/form-data"}
            response = requests.post(url, files=files, headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            print()

    except FileNotFoundError:
        print(f"Test file {file_path} not found")
    except Exception as e:
        print(f"Error during test: {e}")


if __name__ == "__main__":
    test_frontend_like_upload()
