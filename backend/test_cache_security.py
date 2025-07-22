#!/usr/bin/env python3
"""
Test script for cache cleanup endpoint security.

This script tests the authentication and validation for the cache cleanup endpoint.
"""

import pytest
from fastapi.testclient import TestClient
from config import settings

# Import the FastAPI app
from main import app

# Create test client
client = TestClient(app)


def test_cache_cleanup_no_auth():
    """Test cache cleanup without authentication"""
    response = client.post("/cache/cleanup", json={})

    if settings.is_development:
        # Should succeed in development
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    else:
        # Should fail in production
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"


def test_cache_cleanup_with_valid_auth():
    """Test cache cleanup with valid authentication"""
    print("Testing cache cleanup with valid authentication...")

    headers = {"X-API-Key": settings.api_key}
    response = client.post("/cache/cleanup", json={}, headers=headers)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        print("✅ Valid authentication accepted")
        data = response.json()
        print(f"Environment: {data.get('environment', 'unknown')}")
        print(f"Max age days: {data.get('max_age_days', 'unknown')}")
    else:
        print(f"❌ Valid authentication rejected: {response.status_code}")

    print(f"Response: {response.text[:200]}...\n")


def test_cache_cleanup_with_invalid_auth():
    """Test cache cleanup with invalid authentication"""
    print("Testing cache cleanup with invalid authentication...")

    headers = {"X-API-Key": "invalid-key-12345"}
    response = client.post("/cache/cleanup", json={}, headers=headers)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 401:
        print("✅ Invalid authentication correctly rejected")
    else:
        print(
            f"❌ Invalid authentication should return 401, got {response.status_code}"
        )

    print(f"Response: {response.text[:200]}...\n")


def test_cache_cleanup_validation():
    """Test cache cleanup parameter validation"""
    print("Testing parameter validation...")

    headers = {"X-API-Key": settings.api_key}

    # Test invalid max_age_days (too small)
    response = client.post("/cache/cleanup", json={"max_age_days": 0}, headers=headers)
    print(f"max_age_days=0 -> Status: {response.status_code}")
    if response.status_code == 400:
        print("✅ Correctly rejected max_age_days=0")
    else:
        print(f"❌ Should reject max_age_days=0 with 400, got {response.status_code}")

    # Test invalid max_age_days (too large)
    response = client.post(
        "/cache/cleanup", json={"max_age_days": 500}, headers=headers
    )
    print(f"max_age_days=500 -> Status: {response.status_code}")
    if response.status_code == 400:
        print("✅ Correctly rejected max_age_days=500")
    else:
        print(f"❌ Should reject max_age_days=500 with 400, got {response.status_code}")

    # Test valid max_age_days
    response = client.post("/cache/cleanup", json={"max_age_days": 7}, headers=headers)
    print(f"max_age_days=7 -> Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Correctly accepted max_age_days=7")
    else:
        print(f"❌ Should accept max_age_days=7 with 200, got {response.status_code}")

    print()


def test_query_param_auth():
    """Test authentication via query parameter"""
    print("Testing authentication via query parameter...")

    url = f"/cache/cleanup?api_key={settings.api_key}"
    response = client.post(url, json={})
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        print("✅ Query parameter authentication accepted")
    else:
        print(f"❌ Query parameter authentication rejected: {response.status_code}")

    print(f"Response: {response.text[:200]}...\n")


def main():
    """Run all tests"""
    print("🧪 Testing Cache Cleanup Security")
    print(f"Environment: {settings.environment}")
    print(f"Debug mode: {settings.debug}")
    print(f"API Key set: {'Yes' if settings.api_key else 'No'}")
    print(f"Using TestClient for testing")
    print("=" * 50)

    try:
        test_cache_cleanup_no_auth()
        test_cache_cleanup_with_valid_auth()
        test_cache_cleanup_with_invalid_auth()
        test_cache_cleanup_validation()
        test_query_param_auth()

        print("🎉 All tests completed!")

    except Exception as e:
        print(f"❌ Test error: {e}")


if __name__ == "__main__":
    main()
