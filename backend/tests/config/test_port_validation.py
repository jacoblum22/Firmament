#!/usr/bin/env python3
"""
Test script to verify port validation in config.py
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


def test_port_validation():
    """Test port validation in both development and production modes"""

    print("🧪 Testing port validation...")

    # Test cases
    test_cases = [
        # (port_value, environment, should_raise, expected_port)
        ("8000", "development", False, 8000),
        ("8000", "production", False, 8000),
        ("80", "development", False, 80),
        ("65535", "development", False, 65535),
        ("1", "development", False, 1),
        ("invalid", "development", False, 8000),  # fallback to default
        ("invalid", "production", True, None),  # should raise error
        ("0", "development", False, 8000),  # fallback to default
        ("0", "production", True, None),  # should raise error
        ("65536", "development", False, 8000),  # fallback to default
        ("65536", "production", True, None),  # should raise error
        ("-1", "development", False, 8000),  # fallback to default
        ("-1", "production", True, None),  # should raise error
        ("", "development", False, 8000),  # fallback to default
        ("", "production", True, None),  # should raise error
    ]

    for port_value, environment, should_raise, expected_port in test_cases:
        print(f"\n📋 Testing PORT='{port_value}' in {environment} mode...")

        # Set environment variables
        os.environ["PORT"] = port_value
        os.environ["ENVIRONMENT"] = environment

        # Set a valid OpenAI API key for testing to avoid validation errors
        os.environ["OPENAI_API_KEY"] = "sk-test1234567890abcdef"

        # Clear any existing config module to force reload
        if "config" in sys.modules:
            del sys.modules["config"]

        try:
            # Check if config.py exists before importing
            config_path = backend_dir / "config.py"
            if not config_path.exists():
                print(f"❌ config.py not found at {config_path}")
                return False

            from config import Settings, ConfigurationError

            config = Settings()
            actual_port = config.port

            if should_raise:
                print(
                    f"❌ Expected error for PORT='{port_value}' in {environment} mode, but got port {actual_port}"
                )
                return False
            else:
                if actual_port == expected_port:
                    print(
                        f"✅ PORT='{port_value}' in {environment} mode → {actual_port} (expected)"
                    )
                else:
                    print(
                        f"❌ PORT='{port_value}' in {environment} mode → {actual_port} (expected {expected_port})"
                    )
                    return False

        except ConfigurationError as e:
            if should_raise:
                print(
                    f"✅ Expected error for PORT='{port_value}' in {environment} mode: {e}"
                )
            else:
                print(
                    f"❌ Unexpected ConfigurationError for PORT='{port_value}' in {environment} mode: {e}"
                )
                return False
        except Exception as e:
            if should_raise:
                print(
                    f"✅ Expected error for PORT='{port_value}' in {environment} mode: {e}"
                )
            else:
                print(
                    f"❌ Unexpected error for PORT='{port_value}' in {environment} mode: {e}"
                )
                return False

    print("\n🎉 All port validation tests passed!")
    return True


def test_port_edge_cases():
    """Test additional edge cases for port validation"""

    print("\n🧪 Testing port edge cases...")

    # Test with no PORT environment variable
    if "PORT" in os.environ:
        del os.environ["PORT"]
    os.environ["ENVIRONMENT"] = "development"
    os.environ["OPENAI_API_KEY"] = "sk-test1234567890abcdef"

    if "config" in sys.modules:
        del sys.modules["config"]

    from config import Settings

    config = Settings()

    if config.port == 8000:
        print("✅ No PORT env var → default port 8000")
    else:
        print(f"❌ No PORT env var → {config.port} (expected 8000)")
        return False

    # Test with whitespace
    os.environ["PORT"] = "  8080  "
    if "config" in sys.modules:
        del sys.modules["config"]

    from config import Settings

    config = Settings()

    if config.port == 8080:
        print("✅ PORT with whitespace → 8080")
    else:
        print(f"❌ PORT with whitespace → {config.port} (expected 8080)")
        return False

    print("✅ All edge case tests passed!")
    return True


if __name__ == "__main__":
    try:
        # Store original environment
        original_env = {}
        for key in ["PORT", "ENVIRONMENT", "OPENAI_API_KEY"]:
            if key in os.environ:
                original_env[key] = os.environ[key]

        success = test_port_validation() and test_port_edge_cases()

        if success:
            print("\n🎉 All port validation tests completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Some port validation tests failed!")
            sys.exit(1)

    except Exception as e:
        print(f"\n💥 Test script failed with error: {e}")
        sys.exit(1)

    finally:
        # Restore original environment
        for key in ["PORT", "ENVIRONMENT", "OPENAI_API_KEY"]:
            if key in original_env:
                os.environ[key] = original_env[key]
            elif key in os.environ:
                del os.environ[key]
