#!/usr/bin/env python3
"""
Simple test to verify port validation improvements
"""

import os
import sys
import importlib
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


def test_port_validation_simple():
    """Test port validation with various invalid inputs"""

    print("🧪 Testing Port Validation Improvements")
    print("=" * 40)

    # Test cases: (port_value, environment, should_raise, expected_port)
    test_cases = [
        ("8000", "development", False, 8000),
        ("8000", "production", False, 8000),
        ("invalid", "development", False, 8000),  # fallback to default
        ("invalid", "production", True, None),  # should raise error
        ("0", "development", False, 8000),  # fallback to default
        ("0", "production", True, None),  # should raise error
        ("65536", "development", False, 8000),  # fallback to default
        ("65536", "production", True, None),  # should raise error
    ]

    # Store original environment
    original_env = {}
    for key in ["PORT", "ENVIRONMENT", "OPENAI_API_KEY"]:
        if key in os.environ:
            original_env[key] = os.environ[key]

    try:
        for port_value, environment, should_raise, expected_port in test_cases:
            print(f"\n📋 Testing PORT='{port_value}' in {environment} mode...")

            # Set environment variables
            os.environ["PORT"] = port_value
            os.environ["ENVIRONMENT"] = environment
            os.environ["OPENAI_API_KEY"] = "sk-test1234567890abcdef"

            # Force reload of config module
            if "config" in sys.modules:
                del sys.modules["config"]

            try:
                # Import the Settings class
                from config import Settings

                # Create config instance
                config = Settings()

                # Test the port property directly
                if should_raise:
                    try:
                        actual_port = config.port
                        print(
                            f"❌ Expected error for PORT='{port_value}' in {environment} mode, but got port {actual_port}"
                        )
                        return False
                    except Exception as e:
                        print(
                            f"✅ Expected error for PORT='{port_value}' in {environment} mode: {str(e)[:100]}..."
                        )
                        continue
                else:
                    try:
                        actual_port = config.port
                        if actual_port == expected_port:
                            print(
                                f"✅ PORT='{port_value}' in {environment} mode → {actual_port} (expected)"
                            )
                        else:
                            print(
                                f"❌ PORT='{port_value}' in {environment} mode → {actual_port} (expected {expected_port})"
                            )
                            return False
                    except Exception as e:
                        print(
                            f"❌ Unexpected error for PORT='{port_value}' in {environment} mode: {e}"
                        )
                        return False

            except Exception as e:
                if should_raise:
                    print(
                        f"✅ Expected error for PORT='{port_value}' in {environment} mode: {str(e)[:100]}..."
                    )
                else:
                    print(
                        f"❌ Unexpected error for PORT='{port_value}' in {environment} mode: {e}"
                    )
                    return False

    finally:
        # Restore original environment
        for key in ["PORT", "ENVIRONMENT", "OPENAI_API_KEY"]:
            if key in original_env:
                os.environ[key] = original_env[key]
            elif key in os.environ:
                del os.environ[key]

    print("\n🎉 All port validation tests passed!")
    return True


if __name__ == "__main__":
    success = test_port_validation_simple()
    if success:
        print("\n✅ Port validation test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Port validation test failed!")
        sys.exit(1)
