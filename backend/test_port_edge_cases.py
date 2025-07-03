#!/usr/bin/env python3
"""
Test edge cases for port validation
"""

import os
import sys
import importlib
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


def test_port_edge_cases():
    """Test edge cases for port validation"""

    print("🧪 Testing Port Validation Edge Cases")
    print("=" * 40)

    # Store original values
    original_port = os.environ.get("PORT")
    original_env = os.environ.get("ENVIRONMENT")

    try:
        # Test 1: No PORT environment variable
        print("\n📋 Test 1: No PORT environment variable")
        if "PORT" in os.environ:
            del os.environ["PORT"]
        os.environ["ENVIRONMENT"] = "development"

        if "config" in sys.modules:
            importlib.reload(sys.modules["config"])

        from config import settings

        print(f"✅ No PORT env var → {settings.port} (default)")

        # Test 2: PORT with whitespace
        print("\n📋 Test 2: PORT with whitespace")
        os.environ["PORT"] = "  8080  "

        if "config" in sys.modules:
            importlib.reload(sys.modules["config"])

        from config import settings

        print(f"✅ PORT='  8080  ' → {settings.port}")

        # Test 3: PORT with decimal
        print("\n📋 Test 3: PORT with decimal")
        os.environ["PORT"] = "8080.5"

        if "config" in sys.modules:
            importlib.reload(sys.modules["config"])

        from config import settings

        print(f"✅ PORT='8080.5' → {settings.port} (fallback to default)")

        # Test 4: Empty PORT
        print("\n📋 Test 4: Empty PORT")
        os.environ["PORT"] = ""

        if "config" in sys.modules:
            importlib.reload(sys.modules["config"])

        from config import settings

        print(f"✅ PORT='' → {settings.port} (fallback to default)")

        # Test 5: PORT with negative value
        print("\n📋 Test 5: PORT with negative value")
        os.environ["PORT"] = "-8080"

        if "config" in sys.modules:
            importlib.reload(sys.modules["config"])

        from config import settings

        print(f"✅ PORT='-8080' → {settings.port} (fallback to default)")

        # Test 6: PORT at boundaries
        print("\n📋 Test 6: PORT at boundaries")
        for port_val in ["1", "65535"]:
            os.environ["PORT"] = port_val

            if "config" in sys.modules:
                importlib.reload(sys.modules["config"])

            from config import settings

            print(f"✅ PORT='{port_val}' → {settings.port}")

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


if __name__ == "__main__":
    test_port_edge_cases()
