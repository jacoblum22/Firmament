#!/usr/bin/env python3
"""
Demonstration of the datetime.utcnow() deprecation fix
"""

from datetime import datetime, timezone


def test_datetime_approaches():
    """Test old vs new datetime approaches"""

    print("=" * 60)
    print("DATETIME DEPRECATION FIX DEMONSTRATION")
    print("=" * 60)

    # Old approach (deprecated)
    print("\n❌ OLD APPROACH (DEPRECATED):")
    try:
        old_dt = datetime.utcnow()
        old_timestamp = old_dt.isoformat() + "Z"
        print(f"datetime.utcnow(): {old_dt}")
        print(f"Timezone aware: {old_dt.tzinfo is not None}")
        print(f"Final timestamp: {old_timestamp}")
        print("⚠️  This approach is deprecated and returns naive datetime!")
    except Exception as e:
        print(f"Error: {e}")

    # New approach (recommended)
    print("\n✅ NEW APPROACH (RECOMMENDED):")
    try:
        new_dt = datetime.now(timezone.utc)
        new_timestamp = new_dt.isoformat()
        print(f"datetime.now(timezone.utc): {new_dt}")
        print(f"Timezone aware: {new_dt.tzinfo is not None}")
        print(f"Timezone info: {new_dt.tzinfo}")
        print(f"Final timestamp: {new_timestamp}")
        print("✅ This approach returns timezone-aware datetime!")
    except Exception as e:
        print(f"Error: {e}")

    # Show the difference
    print("\n📊 COMPARISON:")
    print(f"Old (naive): {datetime.utcnow()}")
    print(f"New (aware): {datetime.now(timezone.utc)}")

    print("\n💡 BENEFITS OF THE NEW APPROACH:")
    print("1. Timezone-aware datetime objects")
    print("2. No need to manually append 'Z'")
    print("3. ISO format includes timezone offset (+00:00)")
    print("4. Future-proof (not deprecated)")
    print("5. More explicit and clear intent")

    print("\n🔧 CHANGE SUMMARY:")
    print("Before: datetime.utcnow().isoformat() + 'Z'")
    print("After:  datetime.now(timezone.utc).isoformat()")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_datetime_approaches()
