#!/usr/bin/env python3
"""
Test S3 connection in production mode
"""

import os

os.environ["ENVIRONMENT"] = "production"

try:
    from config import Settings
    from utils.s3_storage import S3StorageManager

    print("🧪 Testing S3 Connection in Production Mode")
    print("=" * 50)

    # Load production settings
    settings = Settings()
    print(f"✓ Environment: {settings.environment}")
    print(f"✓ Use S3: {settings.use_s3_storage}")
    print(f"✓ AWS Region: {settings.aws_region}")
    print(f"✓ Bucket: {settings.s3_bucket_name}")

    # Test storage manager
    storage = S3StorageManager(settings)

    # Test basic S3 operations
    test_key = "test/connection-test.txt"
    test_content = b"Hello from StudyMate-v2 production test!"

    print(f"\n📤 Testing file upload...")
    success = storage.upload_file(test_content, test_key, "text/plain")
    if success:
        print(f"✓ Upload successful")
    else:
        print(f"❌ Upload failed")
        exit(1)

    print(f"🔍 Testing file exists...")
    exists = storage.file_exists(test_key)
    if exists:
        print(f"✓ File exists")
    else:
        print(f"❌ File not found")
        exit(1)

    print(f"📥 Testing download...")
    downloaded = storage.download_file(test_key)
    if downloaded == test_content:
        print(f"✓ Download successful and content matches")
    else:
        print(f"❌ Download failed or content mismatch")
        exit(1)

    print(f"🗑️ Testing cleanup...")
    deleted = storage.delete_file(test_key)
    if deleted:
        print(f"✓ File deleted successfully")
    else:
        print(f"❌ Delete failed")
        exit(1)

    print(f"\n🎉 ALL TESTS PASSED!")
    print(f"Your AWS S3 setup is working perfectly!")

except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback

    traceback.print_exc()
