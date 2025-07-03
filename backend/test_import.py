#!/usr/bin/env python3
"""Simple test to check if main.py imports correctly"""

try:
    from main import app

    print("✅ FastAPI app imported successfully")
    print(f"App title: {app.title}")
    print(f"App version: {app.version}")

    # Test settings
    from config import settings

    print(f"Environment: {settings.environment}")
    print(f"Debug mode: {settings.debug}")
    print(f"Allowed origins: {len(settings.allowed_origins)} origins configured")

except Exception as e:
    print(f"❌ Error importing: {e}")
    import traceback

    traceback.print_exc()
