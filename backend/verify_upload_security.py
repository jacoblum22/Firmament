#!/usr/bin/env python3
"""
Simple test verification script for file upload validation.
This script provides quick methods to verify that file upload validation is working.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, cwd=os.getcwd()
        )

        if result.returncode == 0:
            print("✅ PASSED")
            # Show summary line for successful tests
            output_lines = result.stdout.split("\n")
            for line in output_lines:
                if "passed" in line and (
                    "failed" in line or "error" in line or "====" in line
                ):
                    print(f"   {line.strip()}")
                    break
            return True
        else:
            print("❌ FAILED")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def main():
    """Main verification function"""

    print("🔍 FILE UPLOAD VALIDATION VERIFICATION")
    print("=" * 60)
    print("This script verifies that file upload validation is working correctly.")
    print(
        "Make sure you're in the backend directory with the virtual environment activated."
    )

    # Check if we're in the right directory
    if not os.path.exists("utils/file_validator.py"):
        print("\n❌ ERROR: Cannot find utils/file_validator.py")
        print("Please run this script from the backend directory.")
        return False

    if not os.path.exists("venv") and not os.path.exists(".venv"):
        print("\n⚠️  WARNING: No virtual environment detected.")
        print("Consider activating your virtual environment first.")

    # List of tests to run
    tests = [
        {
            "cmd": "python -m pytest tests/utils/test_file_validator.py -v --tb=short",
            "desc": "Unit Tests - FileValidator Class",
        },
        {
            "cmd": "python -m pytest tests/integration/test_file_upload_validation.py -v --tb=short",
            "desc": "Integration Tests - Upload Endpoint",
        },
        {
            "cmd": "python -m pytest tests/utils/test_file_generators.py -v --tb=short",
            "desc": "Test File Generators",
        },
    ]

    results = []

    for test in tests:
        success = run_command(test["cmd"], test["desc"])
        results.append((test["desc"], success))

    # Summary
    print(f"\n{'='*60}")
    print("📊 VERIFICATION SUMMARY")
    print(f"{'='*60}")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for desc, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {desc}")

    print(f"\nOverall: {passed}/{total} test suites passed")

    if passed == total:
        print("\n🎉 SUCCESS! File upload validation is working correctly.")
        print("\nYour system correctly:")
        print("  ✅ Validates file extensions")
        print("  ✅ Enforces file size limits")
        print("  ✅ Checks file signatures/content")
        print("  ✅ Sanitizes malicious filenames")
        print("  ✅ Handles upload endpoint security")

        print("\n🔒 Security Status: SECURE")

    else:
        print(f"\n⚠️  WARNING: {total - passed} test suite(s) failed.")
        print("Please review the failed tests above and fix any issues.")
        print("\n🔒 Security Status: NEEDS ATTENTION")

    return passed == total


def quick_test():
    """Run a quick test to verify basic functionality"""
    print("🚀 QUICK VALIDATION TEST")
    print("=" * 30)

    # Just run the most important unit tests
    success = run_command(
        "python -m pytest tests/utils/test_file_validator.py::TestFileValidator::test_validate_upload_comprehensive -v",
        "Core Upload Validation Test",
    )

    if success:
        print("\n✅ Quick test passed! Basic validation is working.")
    else:
        print("\n❌ Quick test failed. Please run full verification.")

    return success


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Verify file upload validation")
    parser.add_argument("--quick", action="store_true", help="Run only quick tests")

    args = parser.parse_args()

    if args.quick:
        success = quick_test()
    else:
        success = main()

    sys.exit(0 if success else 1)
