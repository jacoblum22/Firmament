"""
Standalone CORS test script that is more reliable and provides better error handling
"""

import json
import time
from typing import Dict, Any

# Conditional imports with availability flags
try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️  Warning: requests module not available. CORS tests will be skipped.")

try:
    import pytest

    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    print("⚠️  Warning: pytest module not available. Using fallback skip mechanism.")

    # Define a fallback skip function if pytest is not available
    class _FallbackSkip:
        def skip(self, reason: str):
            print(f"⏭️  Skipping test: {reason}")
            return

    pytest = _FallbackSkip()


def wait_for_server(
    base_url: str = "http://127.0.0.1:8000", max_attempts: int = 5
) -> bool:
    """Wait for server to be ready"""
    if not REQUESTS_AVAILABLE:
        print("⚠️  Cannot check server status - requests module not available")
        return False

    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{base_url}/health", timeout=2)
            if response.status_code == 200:
                print(f"✅ Server is ready (attempt {attempt + 1})")
                return True
        except Exception:
            print(f"⏳ Waiting for server... (attempt {attempt + 1}/{max_attempts})")
            time.sleep(1)
    return False


def test_server_health():
    """Test that the server health endpoint is working"""
    if not REQUESTS_AVAILABLE:
        pytest.skip("requests module not available")
        return

    base_url = "http://127.0.0.1:8000"

    if not wait_for_server(base_url):
        pytest.skip("Server not available for testing")

    response = requests.get(f"{base_url}/health", timeout=5)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    required_fields = ["status", "environment", "timestamp"]

    for field in required_fields:
        assert field in data, f"Missing required field: {field}"

    assert (
        data["status"] == "healthy"
    ), f"Expected status 'healthy', got {data.get('status')}"

    print(f"✅ Health check passed: {data}")


def test_cors_allowed_origins():
    """Test CORS for allowed origins"""
    if not REQUESTS_AVAILABLE:
        pytest.skip("requests module not available")
        return

    base_url = "http://127.0.0.1:8000"

    if not wait_for_server(base_url):
        pytest.skip("Server not available for testing")

    allowed_origins = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    for origin in allowed_origins:
        headers = {
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        }

        response = requests.options(base_url, headers=headers, timeout=5)

        assert (
            response.status_code == 200
        ), f"CORS failed for allowed origin {origin}: {response.status_code}"

        # Check that the origin is properly echoed back
        assert (
            "access-control-allow-origin" in response.headers
        ), f"Missing CORS origin header for {origin}"
        assert (
            response.headers["access-control-allow-origin"] == origin
        ), f"Wrong origin returned for {origin}"

        # Check required CORS headers
        required_cors_headers = [
            "access-control-allow-methods",
            "access-control-allow-headers",
            "access-control-allow-credentials",
        ]

        for header in required_cors_headers:
            assert (
                header in response.headers
            ), f"Missing CORS header {header} for origin {origin}"

        print(f"✅ CORS test passed for allowed origin: {origin}")


def test_cors_unauthorized_origin():
    """Test CORS for unauthorized origins"""
    if not REQUESTS_AVAILABLE:
        pytest.skip("requests module not available")
        return

    base_url = "http://127.0.0.1:8000"

    if not wait_for_server(base_url):
        pytest.skip("Server not available for testing")

    unauthorized_origins = [
        "http://malicious-site.com",
        "http://evil-domain.net",
        "https://untrusted.example.com",
    ]

    for origin in unauthorized_origins:
        headers = {
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        }

        response = requests.options(base_url, headers=headers, timeout=5)

        # For unauthorized origins, we expect either 400 or the origin to not be echoed back
        if response.status_code == 200:
            # If status is 200, the origin should not be in the allow-origin header
            # or the header should be missing
            if "access-control-allow-origin" in response.headers:
                returned_origin = response.headers["access-control-allow-origin"]
                assert (
                    returned_origin != origin
                ), f"Unauthorized origin {origin} was allowed!"
        else:
            # Status should be 400 for unauthorized origins
            assert (
                response.status_code == 400
            ), f"Expected 400 for unauthorized origin {origin}, got {response.status_code}"

        print(f"✅ CORS properly rejected unauthorized origin: {origin}")


def test_cors_methods_and_headers():
    """Test that CORS allows the expected methods and headers"""
    if not REQUESTS_AVAILABLE:
        pytest.skip("requests module not available")
        return

    base_url = "http://127.0.0.1:8000"

    if not wait_for_server(base_url):
        pytest.skip("Server not available for testing")

    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type,Authorization",
    }

    response = requests.options(base_url, headers=headers, timeout=5)

    assert response.status_code == 200, f"CORS preflight failed: {response.status_code}"

    # Check allowed methods
    allowed_methods = response.headers.get("access-control-allow-methods", "").split(
        ", "
    )
    expected_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]

    for method in expected_methods:
        assert (
            method in allowed_methods
        ), f"Method {method} not in allowed methods: {allowed_methods}"

    # Check that credentials are allowed
    assert (
        response.headers.get("access-control-allow-credentials") == "true"
    ), "Credentials should be allowed"

    print(f"✅ CORS methods and headers test passed")
    print(f"   Allowed methods: {allowed_methods}")
    print(
        f"   Credentials allowed: {response.headers.get('access-control-allow-credentials')}"
    )


if __name__ == "__main__":
    print("🧪 Running Standalone CORS Tests")
    print("=" * 50)

    # Check dependencies before running tests
    if not REQUESTS_AVAILABLE:
        print("\n❌ Cannot run CORS tests: requests module not available")
        print("   Install with: pip install requests")
        exit(1)

    try:
        print("\n1. Testing server health...")
        test_server_health()

        print("\n2. Testing allowed origins...")
        test_cors_allowed_origins()

        print("\n3. Testing unauthorized origins...")
        test_cors_unauthorized_origin()

        print("\n4. Testing methods and headers...")
        test_cors_methods_and_headers()

        print("\n✅ All CORS tests passed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise
