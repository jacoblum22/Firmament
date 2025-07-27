#!/usr/bin/env python3
"""
Test Google OAuth configuration
"""

import os
import sys
from dotenv import load_dotenv

# Set test environment (or make configurable)
os.environ["ENVIRONMENT"] = os.getenv("TEST_ENVIRONMENT", "test")

# Add the backend directory to Python path for imports
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
if os.path.exists(backend_dir):
    sys.path.insert(0, backend_dir)
else:
    raise ImportError("Backend directory not found")

try:
    try:
        from backend.config import Settings
    except ImportError:
        raise ImportError(
            "Could not import 'Settings' from 'backend.config'. Ensure the module exists and is in the Python path."
        )
    from utils.auth import UserAuthManager

    print("🧪 Testing Google OAuth Configuration")
    print("=" * 50)

    settings = Settings()

    # Test configuration
    print(f"✓ Environment: {settings.environment}")
    print(
        f"✓ Google Client ID configured: {'Yes' if settings.google_client_id else 'No'}"
    )
    print(
        f"✓ Google Client Secret configured: {'Yes' if settings.google_client_secret else 'No'}"
    )

    # Test auth manager initialization
    print("\n🔐 Testing UserAuthManager...")
    auth_manager = UserAuthManager(settings)
    print("✓ UserAuthManager initialized successfully")

    # Test Google configuration
    if settings.google_client_id and settings.google_client_secret:
        print("✓ Google OAuth credentials configured")
        print("✓ Client ID: [CONFIGURED]")
        print("✓ Ready for Google authentication")
    else:
        print("❌ Google OAuth credentials missing")

    print("\n📋 Configuration Status:")
    print("✓ Backend OAuth configuration: Loaded")
    if settings.google_client_id and settings.google_client_secret:
        print("✓ Google OAuth credentials: Present")
        print("\n🎉 OAuth credentials are configured!")
    else:
        print("❌ Google OAuth credentials: Missing")
        print("\n⚠️  OAuth credentials need to be configured!")
    print("\n📋 Next steps:")
    print("1. Integrate Google OAuth button in frontend")
    print("2. Test end-to-end authentication flow")
    print("3. Deploy to production environment")

except Exception as e:
    print(f"❌ Error testing Google OAuth: {str(e)}")
    import traceback

    traceback.print_exc()
