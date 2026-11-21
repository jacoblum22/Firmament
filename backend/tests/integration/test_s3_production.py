#!/usr/bin/env python3
"""
Test S3 connection in production mode
"""

import os

os.environ["ENVIRONMENT"] = "production"

try:
    from app.config import Settings
    from utils.storage.s3_storage import S3StorageManager

    print("ðŸ§ª Testing S3 Connection in Production Mode")
    print("=" * 50)

    # Load production settings
    settings = Settings()
    print(f"âœ“ Environment: {settings.environment}")
    print(f"âœ“ Use S3: {settings.use_s3_storage}")
    print(f"âœ“ AWS Region: {settings.aws_region}")
    print(f"âœ“ Bucket: {settings.s3_bucket_name}")

    # Test storage manager
    storage = S3StorageManager(settings)

    # Test basic S3 operations
    test_key = "test/connection-test.txt"
    test_content = b"Hello from StudyMate-v2 production test!"

    print(f"\nðŸ“¤ Testing file upload...")
    success = storage.upload_file(test_content, test_key, "text/plain")
    if success:
        print(f"âœ“ Upload successful")
    else:
        print(f"âŒ Upload failed")
        exit(1)

    print(f"ðŸ” Testing file exists...")
    exists = storage.file_exists(test_key)
    if exists:
        print(f"âœ“ File exists")
    else:
        print(f"âŒ File not found")
        exit(1)

    print(f"ðŸ“¥ Testing download...")
    downloaded = storage.download_file(test_key)
    if downloaded == test_content:
        print(f"âœ“ Download successful and content matches")
    else:
        print(f"âŒ Download failed or content mismatch")
        exit(1)

    print(f"ðŸ—‘ï¸ Testing cleanup...")
    deleted = storage.delete_file(test_key)
    if deleted:
        print(f"âœ“ File deleted successfully")
    else:
        print(f"âŒ Delete failed")
        exit(1)

    print(f"\nðŸŽ‰ ALL TESTS PASSED!")
    print(f"Your AWS S3 setup is working perfectly!")

except Exception as e:
    print(f"âŒ Test failed: {e}")
    import traceback

    traceback.print_exc()

