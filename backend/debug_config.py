#!/usr/bin/env python3
"""
Debug configuration validation to see exactly what's failing
"""

import os
import sys
from dotenv import load_dotenv

# Set production environment
os.environ["ENVIRONMENT"] = "production"

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from config import Settings

    print("🔍 Loading production configuration...")
    settings = Settings()

    print(f"✅ Environment: {settings.environment}")
    print(f"✅ Is Production: {settings.is_production}")
    print(f"✅ Debug: {settings.debug}")

    # Try to validate the configuration
    print("\n🔍 Running configuration validation...")
    try:
        validation_result = settings.validate_configuration()
        print("✅ Configuration validation passed!")
        print(f"Validation result: {validation_result}")
    except Exception as e:
        print(f"❌ Configuration validation failed: {str(e)}")
        print(f"Exception type: {type(e).__name__}")

        # Try to get more details
        if hasattr(e, "args") and e.args:
            print(f"Error details: {e.args}")

    # Test specific configuration values
    print("\n🔍 Checking specific configuration values...")
    print(f"ALLOWED_ORIGINS: {settings.allowed_origins}")
    print(f"TRUSTED_HOSTS: {settings.trusted_hosts}")
    print(f"OpenAI API Key: {'Present' if settings.openai_api_key else 'Missing'}")
    print(f"AWS Access Key: {'Present' if settings.aws_access_key_id else 'Missing'}")
    print(f"S3 Bucket: {settings.s3_bucket_name}")
    print(f"Google Client ID: {settings.google_client_id}")

except Exception as e:
    print(f"❌ Failed to load configuration: {str(e)}")
    print(f"Exception type: {type(e).__name__}")
    import traceback

    traceback.print_exc()
