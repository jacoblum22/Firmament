#!/usr/bin/env python3
"""
Test runner for file upload validation.
Runs all tests and provides a comprehensive report.

Usage:
    python run_upload_tests.py [--verbose] [--manual] [--performance]
"""

import subprocess
import sys
import os
import time
import argparse
from pathlib import Path


class TestRunner:
    """Test runner for upload validation"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results = {}

    def run_command(self, command: list, description: str) -> bool:
        """Run a command and capture results"""

        print(f"\n{'='*60}")
        print(f"Running: {description}")
        print(f"Command: {' '.join(command)}")
        print(f"{'='*60}")

        start_time = time.time()

        try:
            if self.verbose:
                result = subprocess.run(command, cwd=os.getcwd(), check=True)
                success = result.returncode == 0
            else:
                result = subprocess.run(
                    command, cwd=os.getcwd(), capture_output=True, text=True, check=True
                )
                success = result.returncode == 0

                # Show output even in non-verbose mode for important info
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print("STDERR:", result.stderr)

        except subprocess.CalledProcessError as e:
            success = False
            print(f"❌ FAILED: {description}")
            if hasattr(e, "stdout") and e.stdout:
                print("STDOUT:", e.stdout)
            if hasattr(e, "stderr") and e.stderr:
                print("STDERR:", e.stderr)
        except Exception as e:
            success = False
            print(f"❌ ERROR: {str(e)}")

        end_time = time.time()
        duration = end_time - start_time

        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"\n{status} - {description} ({duration:.2f}s)")

        self.results[description] = {
            "success": success,
            "duration": duration,
            "command": " ".join(command),
        }

        return success

    def run_unit_tests(self) -> bool:
        """Run unit tests for file validation"""

        commands = [
            # Test the file validator utility
            (
                ["python", "-m", "pytest", "tests/utils/test_file_validator.py", "-v"],
                "File Validator Unit Tests",
            ),
            # Test file generators
            (
                [
                    "python",
                    "-c",
                    "from tests.utils.test_file_generators import TestFileGenerator; print('File generators work')",
                ],
                "Test File Generator Check",
            ),
        ]

        all_passed = True
        for command, description in commands:
            if not self.run_command(command, description):
                all_passed = False

        return all_passed

    def run_integration_tests(self) -> bool:
        """Run integration tests"""

        commands = [
            # Test upload endpoint integration
            (
                [
                    "python",
                    "-m",
                    "pytest",
                    "tests/integration/test_file_upload_validation.py",
                    "-v",
                ],
                "Upload Endpoint Integration Tests",
            ),
            # Run comprehensive test suite
            (
                [
                    "python",
                    "-m",
                    "pytest",
                    "tests/test_file_upload_comprehensive.py",
                    "-v",
                ],
                "Comprehensive Upload Validation Tests",
            ),
        ]

        all_passed = True
        for command, description in commands:
            if not self.run_command(command, description):
                all_passed = False

        return all_passed

    def run_performance_tests(self) -> bool:
        """Run performance tests"""

        # Create a simple performance test
        perf_test_code = """
import time
from tests.utils.test_file_generators import TestFileGenerator
from utils.file_validator import FileValidator

print("Running performance tests...")

# Test validation speed
start = time.time()
for i in range(10):
    pdf = TestFileGenerator.create_valid_pdf(5.0)  # 5MB files
    FileValidator.validate_upload(pdf, f"test_{i}.pdf")
end = time.time()

avg_time = (end - start) / 10
print(f"Average validation time for 5MB PDF: {avg_time:.3f}s")

if avg_time < 1.0:
    print("✅ Performance test PASSED")
else:
    print("⚠️  Performance test SLOW (but acceptable)")
"""

        command = ["python", "-c", perf_test_code]
        return self.run_command(command, "Performance Tests")

    def run_manual_tests(self) -> bool:
        """Run manual tests against a running server"""

        print("\n" + "=" * 60)
        print("MANUAL TESTING")
        print("=" * 60)
        print("This will test against a running server instance.")
        print("Make sure your StudyMate backend is running on http://localhost:8000")
        print("\nPress Enter to continue, or Ctrl+C to skip...")

        try:
            input()
        except KeyboardInterrupt:
            print("\nSkipping manual tests")
            return True

        command = ["python", "tests/manual_upload_test.py", "--quick"]
        return self.run_command(command, "Manual Upload Tests")

    def check_imports(self) -> bool:
        """Check that all required modules can be imported"""

        import_mappings = {
            "from utils.file_validator import FileValidator": (
                "utils.file_validator",
                "FileValidator",
            ),
            "from tests.utils.test_file_generators import TestFileGenerator": (
                "tests.utils.test_file_generators",
                "TestFileGenerator",
            ),
            "from routes import router": ("routes", "router"),
            "from config import settings": ("config", "settings"),
            "import fastapi": ("fastapi", None),
            "import pytest": ("pytest", None),
        }

        print("\n" + "=" * 60)
        print("CHECKING IMPORTS")
        print("=" * 60)

        all_imports_ok = True
        import importlib

        for import_test, (module_name, attr_name) in import_mappings.items():
            try:
                module = importlib.import_module(module_name)
                if attr_name:
                    getattr(module, attr_name)
                print(f"✅ {import_test}")
            except Exception as e:
                print(f"❌ {import_test} - {e}")
                all_imports_ok = False

        return all_imports_ok

    def generate_final_report(self):
        """Generate a final test report"""

        print("\n" + "=" * 80)
        print("FINAL TEST REPORT")
        print("=" * 80)

        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results.values() if r["success"])
        failed_tests = total_tests - passed_tests
        total_time = sum(r["duration"] for r in self.results.values())

        print(f"Total test suites: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(
            f"Success rate: {(passed_tests/total_tests)*100:.1f}%"
            if total_tests > 0
            else "No tests run"
        )
        print(f"Total time: {total_time:.2f}s")

        print("\nDetailed Results:")
        print("-" * 50)

        for description, result in self.results.items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"{status} {description} ({result['duration']:.2f}s)")

        if failed_tests > 0:
            print("\n⚠️  Some tests failed. Please review the output above.")
            print("Common issues:")
            print(
                "- Missing dependencies (install with: pip install -r requirements.txt)"
            )
            print("- Server not running (for manual tests)")
            print("- Import path issues")
        else:
            print(
                "\n🎉 All tests passed! Your file upload validation is working correctly."
            )

        return failed_tests == 0


def main():
    parser = argparse.ArgumentParser(description="Run file upload validation tests")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show verbose output"
    )
    parser.add_argument(
        "--manual",
        "-m",
        action="store_true",
        help="Include manual tests (requires running server)",
    )
    parser.add_argument(
        "--performance", "-p", action="store_true", help="Include performance tests"
    )
    parser.add_argument("--unit-only", action="store_true", help="Run only unit tests")
    parser.add_argument(
        "--integration-only", action="store_true", help="Run only integration tests"
    )

    args = parser.parse_args()

    # Make sure we're in the right directory (backend)
    current_dir = Path.cwd()
    if current_dir.name == "tests":
        os.chdir(current_dir.parent)
    elif "backend" not in str(current_dir):
        # Try to find backend directory
        backend_dir = current_dir / "backend"
        if backend_dir.exists():
            os.chdir(backend_dir)

    print(f"Working directory: {Path.cwd()}")

    runner = TestRunner(verbose=args.verbose)

    print("FILE UPLOAD VALIDATION TEST SUITE")
    print("=" * 80)
    print("This will test all aspects of the file upload validation system.")

    # Check imports first
    if not runner.check_imports():
        print("\n❌ Import checks failed. Please install dependencies:")
        print("  pip install -r requirements.txt")
        return 1

    success = True

    # Run unit tests
    if not args.integration_only:
        if not runner.run_unit_tests():
            success = False

    # Run integration tests
    if not args.unit_only:
        if not runner.run_integration_tests():
            success = False

    # Run performance tests if requested
    if args.performance:
        if not runner.run_performance_tests():
            success = False

    # Run manual tests if requested
    if args.manual:
        if not runner.run_manual_tests():
            success = False

    # Generate final report
    final_success = runner.generate_final_report()

    return 0 if (success and final_success) else 1


if __name__ == "__main__":
    exit(main())
