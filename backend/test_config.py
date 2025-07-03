#!/usr/bin/env python3
"""
Configuration Test Script
Validates that the configuration system works correctly for different environments.
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


def test_environment_config(env_name):
    """Test configuration for a specific environment."""
    print(f"\n🧪 Testing {env_name.upper()} environment")
    print("-" * 40)

    # Clear any existing environment variable
    if "ENVIRONMENT" in os.environ:
        del os.environ["ENVIRONMENT"]

    # Set environment
    os.environ["ENVIRONMENT"] = env_name

    # Clear the module cache to force reload
    import sys

    if "config" in sys.modules:
        del sys.modules["config"]

    # Import settings (this will reload with new environment)
    from config import Settings

    settings = Settings()

    # Test basic properties
    assert settings.environment == env_name, f"Environment should be {env_name}"

    # Test environment-specific behaviors
    if env_name == "development":
        assert settings.is_development == True
        assert settings.is_production == False
        # Debug should be True in dev (either from env or default)
        print(f"   Debug: {settings.debug}")
        assert settings.host == "127.0.0.1"  # Should default to localhost
        assert settings.reload == True  # Should default to True in dev
        assert settings.log_level == "DEBUG"
        print("✅ Development settings validated")

    elif env_name == "production":
        assert settings.is_production == True
        assert settings.is_development == False
        # Debug should be False in prod (either from env or default)
        print(f"   Debug: {settings.debug}")
        assert settings.host == "0.0.0.0"  # Should default to all interfaces
        assert settings.reload == False  # Should default to False in prod
        assert settings.log_level == "INFO"
        print("✅ Production settings validated")

    # Test CORS settings
    assert len(settings.allowed_origins) > 0, "Should have allowed origins"
    print(f"   CORS Origins: {settings.allowed_origins}")

    # Test rate limiting
    assert settings.rate_limit_calls > 0, "Should have rate limit"
    assert settings.rate_limit_period > 0, "Should have rate limit period"
    print(
        f"   Rate Limit: {settings.rate_limit_calls} calls per {settings.rate_limit_period}s"
    )

    # Test file settings
    assert settings.upload_max_size > 0, "Should have upload size limit"
    print(f"   Max Upload Size: {settings.upload_max_size} bytes")

    return True


def test_config_loading():
    """Test that configuration files are loaded correctly."""
    print("\n🔧 Testing configuration file loading")
    print("-" * 40)

    # Test development config
    dev_env_file = Path(".env.development")
    if dev_env_file.exists():
        print(f"✅ Development config file found: {dev_env_file}")
    else:
        print(f"❌ Development config file missing: {dev_env_file}")
        return False

    # Test production config
    prod_env_file = Path(".env.production")
    if prod_env_file.exists():
        print(f"✅ Production config file found: {prod_env_file}")
    else:
        print(f"❌ Production config file missing: {prod_env_file}")
        return False

    # Test example config
    example_env_file = Path(".env.example")
    if example_env_file.exists():
        print(f"✅ Example config file found: {example_env_file}")
    else:
        print(f"❌ Example config file missing: {example_env_file}")
        return False

    return True


def main():
    """Run all configuration tests."""
    print("🚀 StudyMate Configuration Test Suite")
    print("=" * 50)

    try:
        # Test config file loading
        if not test_config_loading():
            print("\n❌ Configuration file tests failed")
            return 1

        # Test development environment
        if not test_environment_config("development"):
            print("\n❌ Development environment tests failed")
            return 1

        # Test production environment
        if not test_environment_config("production"):
            print("\n❌ Production environment tests failed")
            return 1

        print("\n🎉 All configuration tests passed!")
        print("\n📝 Summary:")
        print("   ✅ Configuration files exist")
        print("   ✅ Development environment configured correctly")
        print("   ✅ Production environment configured correctly")
        print("   ✅ Environment-specific settings work properly")

        return 0

    except Exception as e:
        print(f"\n❌ Configuration test failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
