#!/usr/bin/env python3
"""
Health check script for StudyMate API
This script performs a health check without requiring curl
"""

import sys
import urllib.request
import urllib.error
import json


def check_health():
    """Check if the StudyMate API is healthy"""
    try:
        # Make a request to the health endpoint
        with urllib.request.urlopen(
            "http://localhost:8000/health", timeout=10
        ) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                if data.get("status") == "healthy":
                    print("✅ Health check passed")
                    return True
                else:
                    print(f"❌ Health check failed: status is {data.get('status')}")
                    return False
            else:
                print(f"❌ Health check failed: HTTP {response.status}")
                return False
    except urllib.error.URLError as e:
        print(f"❌ Health check failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


if __name__ == "__main__":
    if check_health():
        sys.exit(0)
    else:
        sys.exit(1)
