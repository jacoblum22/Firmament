"""
Test script to verify CORS configuration
"""

import requests
import json


def test_cors_preflight(
    base_url="http://localhost:8000", origin="http://localhost:5173"
):
    """Test CORS preflight request"""
    print(f"Testing CORS preflight for {origin} -> {base_url}")

    headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type",
    }

    try:
        response = requests.options(base_url, headers=headers)
        print(f"Status Code: {response.status_code}")
        print("Response Headers:")
        for key, value in response.headers.items():
            if key.lower().startswith("access-control"):
                print(f"  {key}: {value}")

        if response.status_code == 200:
            print("✅ CORS preflight successful")
        else:
            print("❌ CORS preflight failed")

    except Exception as e:
        print(f"❌ Error testing CORS: {e}")


def test_health_endpoint(base_url="http://localhost:8000"):
    """Test health endpoint"""
    print(f"\nTesting health endpoint: {base_url}/health")

    try:
        response = requests.get(f"{base_url}/health")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            print("✅ Health check successful")
        else:
            print("❌ Health check failed")

    except Exception as e:
        print(f"❌ Error testing health endpoint: {e}")


if __name__ == "__main__":
    # Test development setup
    print("=== Testing Development CORS ===")
    test_cors_preflight()
    test_health_endpoint()

    # Test with different origins
    print("\n=== Testing Different Origins ===")
    test_cors_preflight(origin="http://localhost:3000")
    test_cors_preflight(origin="http://127.0.0.1:5173")

    # Test with unauthorized origin
    print("\n=== Testing Unauthorized Origin ===")
    test_cors_preflight(origin="http://malicious-site.com")
