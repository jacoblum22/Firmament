#!/usr/bin/env python3
"""
Test edge cases for port validation
"""

import os
import sys
from pathlib import Path

# Add the parent directory to path to import test utilities
test_dir = Path(__file__).parent.parent
sys.path.insert(0, str(test_dir))

from tests.utils.test_config_helper import import_config_settings, ConfigTestContext


def test_port_edge_cases():
    """Test edge cases for port validation"""

    print("🧪 Testing Port Validation Edge Cases")
    print("=" * 40)

    # Store original values
    original_port = os.environ.get("PORT")
    original_env = os.environ.get("ENVIRONMENT")
    original_openai = os.environ.get("OPENAI_API_KEY")

    try:
        # Test 1: No PORT environment variable
        print("\n📋 Test 1: No PORT environment variable")
        os.environ["ENVIRONMENT"] = "development"
        os.environ["OPENAI_API_KEY"] = "sk-test1234567890abcdef"
        if "PORT" in os.environ:
            del os.environ["PORT"]

        Settings = import_config_settings()
        config = Settings()
        assert (
            config.port == 8000
        ), f"No PORT env var should default to 8000, got {config.port}"
        print(f"✅ No PORT env var → {config.port} (default)")

        # Test 2: PORT with whitespace
        print("\n📋 Test 2: PORT with whitespace")
        os.environ["PORT"] = "  8080  "
        Settings = import_config_settings()
        config = Settings()
        assert (
            config.port == 8080
        ), f"PORT with whitespace should be 8080, got {config.port}"
        print(f"✅ PORT='  8080  ' → {config.port}")

        # Test 3: PORT with decimal
        print("\n📋 Test 3: PORT with decimal")
        os.environ["PORT"] = "8080.5"
        Settings = import_config_settings()
        config = Settings()
        assert (
            config.port == 8000
        ), f"PORT with decimal should fallback to 8000, got {config.port}"
        print(f"✅ PORT='8080.5' → {config.port} (fallback to default)")

        # Test 4: Empty PORT
        print("\n📋 Test 4: Empty PORT")
        os.environ["PORT"] = ""
        Settings = import_config_settings()
        config = Settings()
        assert (
            config.port == 8000
        ), f"Empty PORT should fallback to 8000, got {config.port}"
        print(f"✅ PORT='' → {config.port} (fallback to default)")

        # Test 5: PORT with negative value
        print("\n📋 Test 5: PORT with negative value")
        os.environ["PORT"] = "-8080"
        Settings = import_config_settings()
        config = Settings()
        assert (
            config.port == 8000
        ), f"Negative PORT should fallback to 8000, got {config.port}"
        print(f"✅ PORT='-8080' → {config.port} (fallback to default)")

        # Test 6: PORT at boundaries
        print("\n📋 Test 6: PORT at boundaries")
        for port_val in ["1", "65535"]:
            os.environ["PORT"] = port_val
            Settings = import_config_settings()
            config = Settings()
            expected_port = int(port_val)
            assert (
                config.port == expected_port
            ), f"PORT='{port_val}' should be {expected_port}, got {config.port}"
            print(f"✅ PORT='{port_val}' → {config.port}")

        print("\n🎉 All edge case tests completed successfully!")

    finally:
        # Restore original values
        if original_port is not None:
            os.environ["PORT"] = original_port
        elif "PORT" in os.environ:
            del os.environ["PORT"]

        if original_env is not None:
            os.environ["ENVIRONMENT"] = original_env
        elif "ENVIRONMENT" in os.environ:
            del os.environ["ENVIRONMENT"]

        if original_openai is not None:
            os.environ["OPENAI_API_KEY"] = original_openai
        elif "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]


if __name__ == "__main__":
    test_port_edge_cases()
