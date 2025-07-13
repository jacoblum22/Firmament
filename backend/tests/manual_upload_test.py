#!/usr/bin/env python3
"""
Manual testing script for file upload validation.
This script helps verify the upload system works correctly by:
1. Generating test files
2. Testing them against the upload endpoint
3. Providing detailed reports

Usage:
    python manual_upload_test.py [--server-url http://localhost:8000] [--output-dir ./test_files]
"""

import argparse
import requests
import os
import tempfile
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple
import sys

# Add the parent directory to Python path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.utils.test_file_generators import TestFileGenerator


class UploadTester:
    """Manual upload testing utility"""

    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url.rstrip("/")
        self.upload_url = f"{self.server_url}/upload"
        self.results = []

    def test_upload(self, filename: str, content: bytes) -> Dict:
        """Test uploading a single file"""

        print(f"Testing upload: {filename} ({len(content)} bytes)")

        files = {"file": (filename, content)}

        try:
            start_time = time.time()
            response = requests.post(self.upload_url, files=files, timeout=30)
            end_time = time.time()

            upload_time = end_time - start_time

            result = {
                "filename": filename,
                "size_bytes": len(content),
                "size_mb": len(content) / (1024 * 1024),
                "status_code": response.status_code,
                "upload_time": upload_time,
                "success": response.status_code == 200,
                "response": (
                    response.json()
                    if response.headers.get("content-type", "").startswith(
                        "application/json"
                    )
                    else response.text
                ),
            }

            if response.status_code == 200:
                print(
                    f"  ✅ SUCCESS: {response.json().get('message', 'Upload accepted')}"
                )
            else:
                print(f"  ❌ FAILED: {response.status_code} - {result['response']}")

        except requests.exceptions.RequestException as e:
            result = {
                "filename": filename,
                "size_bytes": len(content),
                "size_mb": len(content) / (1024 * 1024),
                "status_code": None,
                "upload_time": None,
                "success": False,
                "response": f"Request failed: {str(e)}",
            }
            print(f"  ❌ ERROR: {str(e)}")

        self.results.append(result)
        return result

    def test_valid_files(self):
        """Test valid files that should be accepted"""

        print("\n" + "=" * 50)
        print("TESTING VALID FILES")
        print("=" * 50)

        # Test small valid files
        test_cases = [
            ("small_document.pdf", TestFileGenerator.create_valid_pdf(1.0)),
            ("lecture_notes.txt", TestFileGenerator.create_valid_text(0.1)),
            ("audio_recording.mp3", TestFileGenerator.create_valid_mp3(2.0)),
            ("interview.wav", TestFileGenerator.create_valid_wav(5.0)),
            ("music.m4a", TestFileGenerator.create_valid_m4a(3.0)),
        ]

        for filename, content in test_cases:
            self.test_upload(filename, content)
            time.sleep(0.5)  # Brief pause between uploads

    def test_malicious_files(self):
        """Test malicious files that should be rejected"""

        print("\n" + "=" * 50)
        print("TESTING MALICIOUS FILES (should be rejected)")
        print("=" * 50)

        malicious_files = TestFileGenerator.create_malicious_files()

        for filename, content in malicious_files.items():
            self.test_upload(filename, content)
            time.sleep(0.5)

    def test_oversized_files(self):
        """Test oversized files that should be rejected"""

        print("\n" + "=" * 50)
        print("TESTING OVERSIZED FILES (should be rejected)")
        print("=" * 50)

        # Create files that exceed limits
        test_cases = [
            (
                "huge_document.pdf",
                TestFileGenerator.create_valid_pdf(60.0),
            ),  # Over 50MB
            (
                "massive_text.txt",
                TestFileGenerator.create_valid_text(15.0),
            ),  # Over 10MB
        ]

        for filename, content in test_cases:
            self.test_upload(filename, content)
            time.sleep(1.0)  # Longer pause for large files

    def test_edge_cases(self):
        """Test edge case files"""

        print("\n" + "=" * 50)
        print("TESTING EDGE CASES")
        print("=" * 50)

        edge_files = TestFileGenerator.create_edge_case_files()

        for filename, content in edge_files.items():
            self.test_upload(filename, content)
            time.sleep(0.5)

    def test_filename_security(self):
        """Test filename security"""

        print("\n" + "=" * 50)
        print("TESTING FILENAME SECURITY")
        print("=" * 50)

        pdf_content = TestFileGenerator.create_valid_pdf(0.5)

        dangerous_names = [
            "../../../etc/passwd.pdf",
            "file<script>alert('xss')</script>.pdf",
            "file|dangerous|chars.pdf",
            "file:with:colons.pdf",
            "file*with*wildcards.pdf",
            "normal_file.pdf",  # This should work
        ]

        for filename in dangerous_names:
            self.test_upload(filename, pdf_content)
            time.sleep(0.5)

    def test_server_connectivity(self) -> bool:
        """Test if server is reachable"""

        print(f"Testing server connectivity to {self.server_url}")

        try:
            response = requests.get(f"{self.server_url}/docs", timeout=10)
            if response.status_code == 200:
                print("✅ Server is reachable")
                return True
            else:
                print(f"⚠️  Server responded with status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot reach server: {str(e)}")
            print("\nPlease make sure the StudyMate backend is running:")
            print("  cd backend")
            print("  python -m uvicorn main:app --reload")
            return False

    def generate_report(self) -> str:
        """Generate a detailed test report"""

        if not self.results:
            return "No test results available"

        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - successful_tests

        report = []
        report.append("FILE UPLOAD VALIDATION TEST REPORT")
        report.append("=" * 50)
        report.append(f"Total tests: {total_tests}")
        report.append(f"Successful: {successful_tests}")
        report.append(f"Failed: {failed_tests}")
        report.append(f"Success rate: {(successful_tests/total_tests)*100:.1f}%")
        report.append("")

        # Categorize results
        valid_file_results = []
        malicious_file_results = []
        oversized_file_results = []
        edge_case_results = []

        for result in self.results:
            filename = result["filename"]
            if any(
                name in filename
                for name in ["small_", "lecture_", "audio_", "interview_", "music_"]
            ):
                valid_file_results.append(result)
            elif any(name in filename for name in ["fake_", "malicious"]):
                malicious_file_results.append(result)
            elif any(name in filename for name in ["huge_", "massive_", "large_"]):
                oversized_file_results.append(result)
            else:
                edge_case_results.append(result)

        # Report on valid files
        if valid_file_results:
            report.append("VALID FILES (should succeed):")
            report.append("-" * 30)
            for result in valid_file_results:
                status = "✅ PASS" if result["success"] else "❌ FAIL"
                report.append(
                    f"{status} {result['filename']} ({result['size_mb']:.1f}MB)"
                )
            report.append("")

        # Report on malicious files
        if malicious_file_results:
            report.append("MALICIOUS FILES (should be rejected):")
            report.append("-" * 30)
            for result in malicious_file_results:
                status = (
                    "✅ PASS" if not result["success"] else "❌ FAIL"
                )  # Inverted for malicious files
                report.append(
                    f"{status} {result['filename']} - Rejected: {not result['success']}"
                )
            report.append("")

        # Report on oversized files
        if oversized_file_results:
            report.append("OVERSIZED FILES (should be rejected):")
            report.append("-" * 30)
            for result in oversized_file_results:
                status = (
                    "✅ PASS" if not result["success"] else "❌ FAIL"
                )  # Inverted for oversized files
                report.append(
                    f"{status} {result['filename']} ({result['size_mb']:.1f}MB) - Rejected: {not result['success']}"
                )
            report.append("")

        # Performance summary
        upload_times = [
            r["upload_time"] for r in self.results if r["upload_time"] is not None
        ]
        if upload_times:
            avg_time = sum(upload_times) / len(upload_times)
            max_time = max(upload_times)
            report.append("PERFORMANCE:")
            report.append("-" * 30)
            report.append(f"Average upload time: {avg_time:.2f}s")
            report.append(f"Maximum upload time: {max_time:.2f}s")
            report.append("")

        # Detailed failure analysis
        failures = [r for r in self.results if not r["success"]]
        if failures:
            report.append("DETAILED FAILURE ANALYSIS:")
            report.append("-" * 30)
            for failure in failures:
                report.append(f"File: {failure['filename']}")
                report.append(f"  Size: {failure['size_mb']:.1f}MB")
                report.append(f"  Status: {failure['status_code']}")
                report.append(f"  Response: {failure['response']}")
                report.append("")

        return "\n".join(report)

    def save_results(self, output_file: str):
        """Save detailed results to JSON file"""

        with open(output_file, "w") as f:
            json.dump(
                {
                    "test_results": self.results,
                    "summary": {
                        "total_tests": len(self.results),
                        "successful_tests": sum(
                            1 for r in self.results if r["success"]
                        ),
                        "failed_tests": sum(
                            1 for r in self.results if not r["success"]
                        ),
                        "test_timestamp": time.time(),
                    },
                },
                f,
                indent=2,
            )

        print(f"\nDetailed results saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Manual test for file upload validation"
    )
    parser.add_argument(
        "--server-url",
        default="http://localhost:8000",
        help="URL of the StudyMate backend server",
    )
    parser.add_argument(
        "--output-dir", default="./test_output", help="Directory to save test results"
    )
    parser.add_argument(
        "--quick", action="store_true", help="Run only essential tests (faster)"
    )

    args = parser.parse_args()

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Initialize tester
    tester = UploadTester(args.server_url)

    # Test server connectivity first
    if not tester.test_server_connectivity():
        return 1

    print(f"\nStarting upload validation tests...")
    print(f"Server: {args.server_url}")
    print(f"Output directory: {args.output_dir}")

    # Run tests
    start_time = time.time()

    tester.test_valid_files()
    tester.test_malicious_files()

    if not args.quick:
        tester.test_oversized_files()
        tester.test_edge_cases()
        tester.test_filename_security()

    end_time = time.time()

    # Generate and display report
    print("\n" + "=" * 50)
    print("TEST COMPLETE")
    print("=" * 50)
    print(f"Total test time: {end_time - start_time:.2f} seconds")
    print("\n" + tester.generate_report())

    # Save detailed results
    results_file = os.path.join(
        args.output_dir, f"upload_test_results_{int(time.time())}.json"
    )
    tester.save_results(results_file)

    # Generate test files for manual inspection
    test_files_dir = os.path.join(args.output_dir, "test_files")
    generated_dir = TestFileGenerator.save_test_files_to_disk(test_files_dir)
    print(f"Test files generated in: {generated_dir}")

    return 0


if __name__ == "__main__":
    exit(main())
