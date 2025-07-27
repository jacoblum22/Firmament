#!/usr/bin/env python3
"""
Test the updated routes with authentication and S3 integration
"""


def test_imports():
    try:
        print("🧪 Testing imports...")

        # Test config
        from config import Settings

        print("✓ Config imported")

        # Test storage
        from utils.s3_storage import get_storage_manager

        print("✓ Storage manager imported")

        # Test auth
        from utils.auth import get_auth_manager

        print("✓ Auth manager imported")

        # Test routes (this is the big test)
        from routes import router

        print("✓ Routes imported successfully")

        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_auth_routes():
    try:
        print("\n🔐 Testing authentication setup...")

        from utils.auth import get_auth_manager

        auth_manager = get_auth_manager()

        # Test content hash (should be same for same content)
        content = b"test content for hash"
        hash1 = auth_manager.get_user_content_hash("user1", content)
        hash2 = auth_manager.get_user_content_hash("user2", content)

        if hash1 == hash2:
            print("✓ Hybrid sharing: Same content hash for different users")
        else:
            print("❌ Content hashes differ (should be same)")
            return False

        # Test user storage paths (should be different)
        path1 = auth_manager.get_user_storage_path("user1", hash1, "uploads")
        path2 = auth_manager.get_user_storage_path("user2", hash1, "uploads")

        if path1 != path2:
            print("✓ User isolation: Different storage paths")
            print(f"  User 1: {path1}")
            print(f"  User 2: {path2}")
        else:
            print("❌ Storage paths are same (should be different)")
            return False

        # Test shared cache
        shared_path = auth_manager.get_shared_cache_path(hash1)
        print(f"✓ Shared cache: {shared_path}")

        return True
    except Exception as e:
        print(f"❌ Auth test error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_app_startup():
    try:
        print("\n🚀 Testing FastAPI app startup...")

        from fastapi import FastAPI
        from routes import router

        # Create test app
        app = FastAPI(title="StudyMate-v2 Test")
        app.include_router(router)

        print("✓ FastAPI app created with routes")

        # Check that we have the new auth routes
        route_paths = []
        for route in app.routes:
            if hasattr(route, "path"):
                try:
                    route_paths.append(getattr(route, "path"))
                except AttributeError:
                    continue

        auth_routes = [r for r in route_paths if r.startswith("/auth")]

        if auth_routes:
            print(f"✓ Authentication routes found: {auth_routes}")
        else:
            print("❌ No authentication routes found")
            return False

        return True
    except Exception as e:
        print(f"❌ App startup error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    print("🧪 StudyMate-v2 Integration Test")
    print("Testing authentication, storage, and route integration")
    print("=" * 60)

    tests = [
        ("Imports", test_imports),
        ("Authentication", test_auth_routes),
        ("App Startup", test_app_startup),
    ]

    passed = 0
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")

    print("\n" + "=" * 60)
    print(f"📊 Results: {passed}/{len(tests)} tests passed")

    if passed == len(tests):
        print("🎉 All tests passed! System integration looks good.")
        print("\n📋 Next steps:")
        print("1. Set up AWS account and S3 bucket")
        print("2. Set up Google OAuth credentials")
        print("3. Update .env.production with real credentials")
        print("4. Test file upload with authentication")
    else:
        print("⚠️  Some tests failed. Check output above.")


if __name__ == "__main__":
    main()
