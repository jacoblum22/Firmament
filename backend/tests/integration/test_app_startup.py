#!/usr/bin/env python3
"""
Quick test to verify the FastAPI app can be created and routes are accessible
"""


def test_app_creation():
    try:
        print("🚀 Testing FastAPI app creation...")

        # Import main app
        import app.main as main

        # Check if app was created
        if hasattr(main, "app"):
            print("✓ FastAPI app created successfully")

            # Check for our new routes
            routes = []
            for route in main.app.routes:
                if hasattr(route, "path"):
                    try:
                        routes.append(getattr(route, "path"))
                    except AttributeError:
                        continue

            auth_routes = [r for r in routes if "/auth" in r]
            upload_routes = [r for r in routes if "/upload" in r]

            print(f"✓ Found {len(auth_routes)} auth routes: {auth_routes}")
            print(f"✓ Found {len(upload_routes)} upload routes: {upload_routes}")

            return True
        else:
            print("❌ FastAPI app not found in main module")
            return False

    except Exception as e:
        print(f"❌ App creation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🧪 FastAPI App Creation Test")
    print("=" * 40)

    if test_app_creation():
        print("\n🎉 FastAPI app is ready!")
        print("\n📋 You can now:")
        print("1. Start the server with: python main.py")
        print("2. Test routes at: http://localhost:8000/docs")
        print("3. Set up AWS and Google OAuth credentials")
    else:
        print("\n❌ App creation failed. Check the errors above.")
