#!/usr/bin/env python3
"""
Test authentication and configuration for StudyMate-v2
"""

import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))


def test_config():
    """Test configuration loading"""
    print("🔧 Testing Configuration")
    print("=" * 30)

    try:
        from config import Settings

        settings = Settings()

        print(f"✓ Configuration loaded successfully")
        print(f"  - Environment: {settings.environment}")
        print(f"  - Debug: {settings.debug}")
        print(f"  - Use S3: {settings.use_s3_storage}")
        print(
            f"  - Google Client ID set: {'Yes' if settings.google_client_id else 'No'}"
        )
        print(f"  - OpenAI API Key set: {'Yes' if settings.openai_api_key else 'No'}")

        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_auth():
    """Test authentication module"""
    print("\n🔐 Testing Authentication")
    print("=" * 30)

    try:
        from utils.auth import UserAuthManager
        from config import Settings

        settings = Settings()
        auth_manager = UserAuthManager(settings)

        print(f"✓ Authentication manager initialized")

        # Test user-specific hash (should be same for same content)
        test_content = b"Hello, this is test content!"
        hash1 = auth_manager.get_user_content_hash("user1", test_content)
        hash2 = auth_manager.get_user_content_hash("user2", test_content)

        if hash1 == hash2:
            print(f"✓ Hybrid sharing works - same content hash for different users")
            print(f"  Content hash: {hash1}")
        else:
            print(f"❌ Content hash differs between users (should be same)")
            return False

        # Test user-specific storage paths (should be different)
        path1 = auth_manager.get_user_storage_path("user1", hash1, "cache")
        path2 = auth_manager.get_user_storage_path("user2", hash1, "cache")

        if path1 != path2:
            print(f"✓ User isolation works - different storage paths")
            print(f"  User 1 path: {path1}")
            print(f"  User 2 path: {path2}")
        else:
            print(f"❌ Storage paths are same (should be different)")
            return False

        # Test shared cache path
        shared_path = auth_manager.get_shared_cache_path(hash1)
        print(f"✓ Shared cache path: {shared_path}")

        return True
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False


def test_storage_integration():
    """Test storage and auth integration"""
    print("\n📦 Testing Storage + Auth Integration")
    print("=" * 40)

    try:
        from utils.s3_storage import S3StorageManager
        from utils.auth import UserAuthManager
        from config import Settings

        settings = Settings()
        storage = S3StorageManager(settings)
        auth = UserAuthManager(settings)

        # Simulate user file upload
        user_id = "test_user_123"
        file_content = b"This is a test file for user isolation testing!"
        content_hash = auth.get_user_content_hash(user_id, file_content)

        # Get user-specific storage path
        storage_path = auth.get_user_storage_path(user_id, content_hash, "cache")
        full_key = storage_path + "test_file.txt"

        print(f"✓ Generated user-specific storage key: {full_key}")

        # Upload file
        success = storage.upload_file(file_content, full_key, "text/plain")
        if success:
            print(f"✓ File uploaded to user-specific location")
        else:
            print(f"❌ File upload failed")
            return False

        # Verify file exists
        exists = storage.file_exists(full_key)
        if exists:
            print(f"✓ File exists in user-specific location")
        else:
            print(f"❌ File not found in user-specific location")
            return False

        # Download and verify
        downloaded = storage.download_file(full_key)
        if downloaded == file_content:
            print(f"✓ File downloaded and content verified")
        else:
            print(f"❌ Downloaded content doesn't match")
            return False

        # Clean up
        storage.delete_file(full_key)
        print(f"✓ Test file cleaned up")

        return True
    except Exception as e:
        print(f"❌ Storage + Auth integration test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🧪 StudyMate-v2 System Integration Test")
    print("This tests configuration, authentication, and storage integration.")
    print()

    tests = [
        ("Configuration", test_config),
        ("Authentication", test_auth),
        ("Storage + Auth", test_storage_integration),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Your StudyMate-v2 system is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the output above.")


if __name__ == "__main__":
    main()
