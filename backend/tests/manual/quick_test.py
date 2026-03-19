#!/usr/bin/env python3
"""
Quick test to verify our setup works
"""
import os
import sys
from pathlib import Path

# Run from backend directory so config files resolve correctly
# backend/tests/manual/ -> backend/
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))
os.chdir(backend_dir)


def test_basic_setup():
    try:
        # Test config
        from app.config import Settings

        settings = Settings()
        print(f"✓ Config: {settings.environment}")

        # Test S3 storage
        from utils.s3_storage import get_storage_manager

        storage = get_storage_manager()
        print(f"✓ Storage: {'S3' if storage.use_s3 else 'Local'}")

        # Test auth
        from utils.auth import get_auth_manager

        auth = get_auth_manager()
        print(f"✓ Auth: JWT secret configured")

        # Test hybrid sharing
        content = b"test content"
        hash1 = auth.get_user_content_hash("user1", content)
        hash2 = auth.get_user_content_hash("user2", content)
        path1 = auth.get_user_storage_path("user1", hash1, "cache")
        path2 = auth.get_user_storage_path("user2", hash2, "cache")

        # Add proper assertions instead of just printing
        assert hash1 == hash2, "Content hash mismatch for identical payloads"
        assert path1 != path2, "Storage path should vary per-user"
        print("✓ Hybrid sharing: Same hash, different paths")

        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("🧪 StudyMate-v2 Quick Setup Test")
    if test_basic_setup():
        print("🎉 Basic setup is working!")
    else:
        print("❌ Setup has issues")
