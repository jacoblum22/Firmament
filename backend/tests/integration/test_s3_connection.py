#!/usr/bin/env python3
"""
S3 Connection Test for StudyMate-v2

This script tests the AWS S3 configuration to ensure everything is working properly.
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the path so we can import our modules
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from config import Settings
    from utils.s3_storage import S3StorageManager
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the backend directory and have installed dependencies.")
    sys.exit(1)


def test_s3_connection():
    """Test S3 connection and basic operations"""
    print("🧪 Testing S3 Connection for StudyMate-v2")
    print("=" * 50)

    # Initialize settings
    try:
        settings = Settings()
        print(f"✓ Configuration loaded")
        print(f"  - Environment: {settings.environment}")
        print(f"  - Use S3: {settings.use_s3_storage}")
        if settings.use_s3_storage:
            print(f"  - S3 Bucket: {settings.s3_bucket_name}")
            print(f"  - AWS Region: {settings.aws_region}")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

    # Initialize storage manager
    try:
        storage = S3StorageManager(settings)
        print(f"✓ Storage manager initialized")
    except Exception as e:
        print(f"❌ Storage manager initialization failed: {e}")
        return False

    # Test file upload
    test_key = "test/connection-test.txt"
    test_content = b"Hello from StudyMate-v2! This is a test file."

    try:
        print(f"📤 Testing file upload...")
        success = storage.upload_file(test_content, test_key, "text/plain")
        if success:
            print(f"✓ File uploaded successfully")
        else:
            print(f"❌ File upload failed")
            return False
    except Exception as e:
        print(f"❌ Upload test failed: {e}")
        return False

    # Test file exists
    try:
        print(f"🔍 Testing file existence check...")
        exists = storage.file_exists(test_key)
        if exists:
            print(f"✓ File existence check passed")
        else:
            print(f"❌ File existence check failed")
            return False
    except Exception as e:
        print(f"❌ Existence check failed: {e}")
        return False

    # Test file download
    try:
        print(f"📥 Testing file download...")
        downloaded_content = storage.download_file(test_key)
        if downloaded_content == test_content:
            print(f"✓ File downloaded successfully and content matches")
        else:
            print(f"❌ Downloaded content doesn't match original")
            return False
    except Exception as e:
        print(f"❌ Download test failed: {e}")
        return False

    # Test file deletion
    try:
        print(f"🗑️  Testing file deletion...")
        success = storage.delete_file(test_key)
        if success:
            print(f"✓ File deleted successfully")
        else:
            print(f"❌ File deletion failed")
            return False
    except Exception as e:
        print(f"❌ Deletion test failed: {e}")
        return False

    # Final verification
    try:
        print(f"🔍 Verifying file was deleted...")
        exists = storage.file_exists(test_key)
        if not exists:
            print(f"✓ File deletion verified")
        else:
            print(f"❌ File still exists after deletion")
            return False
    except Exception as e:
        print(f"❌ Final verification failed: {e}")
        return False

    return True


def main():
    """Main test function"""
    print("🔧 StudyMate-v2 S3 Configuration Test")
    print("This will test your S3 setup and configuration.")
    print()

    # Check if we're using S3 or local storage
    settings = Settings()
    if not settings.use_s3_storage:
        print("ℹ️  S3 storage is disabled. Testing local storage fallback...")

    print()

    # Run the test
    success = test_s3_connection()

    print()
    print("=" * 50)
    if success:
        print("🎉 All tests passed! Your S3 configuration is working correctly.")
        print()
        if settings.use_s3_storage:
            print("Your StudyMate application is ready to use AWS S3 for storage.")
        else:
            print("Your StudyMate application is ready to use local storage.")
            print("To enable S3, set USE_S3_STORAGE=true in your environment file.")
    else:
        print("❌ Some tests failed. Please check your configuration.")
        print()
        if settings.use_s3_storage:
            print("Troubleshooting tips:")
            print("1. Verify your AWS credentials are correct")
            print("2. Check that your S3 bucket exists and is accessible")
            print("3. Ensure your IAM user has S3 permissions")
            print("4. Check AWS region configuration")
        else:
            print("Check file permissions and disk space for local storage.")


if __name__ == "__main__":
    main()
