#!/usr/bin/env python3

import requests
import os


def test_upload():
    """Test file upload to check for 422 errors"""
    url = "http://localhost:8000/upload"

    # Test with an existing file
    file_path = "uploads/normal_file.pdf"

    if not os.path.exists(file_path):
        print(f"Test file {file_path} not found. Available files:")
        if os.path.exists("uploads"):
            for f in os.listdir("uploads"):
                print(f"  - {f}")
        return

    try:
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, "application/pdf")}

            print(f"Testing upload of {file_path}...")
            response = requests.post(url, files=files)

            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            print(f"Response: {response.text}")

            if response.status_code == 422:
                print("\n❌ 422 Unprocessable Entity error detected!")
                try:
                    error_data = response.json()
                    print(f"Error details: {error_data}")
                except:
                    print(f"Raw error response: {response.text}")
            elif response.status_code == 200:
                print("\n✅ Upload successful!")
            else:
                print(f"\n⚠️  Unexpected status code: {response.status_code}")

    except Exception as e:
        print(f"Error during test: {e}")


if __name__ == "__main__":
    test_upload()
