#!/usr/bin/env python3
"""
Test script for the content-based caching system.
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.content_cache import ContentCache


def test_cache_functionality():
    """Test the basic caching functionality."""
    print("Testing content-based caching system...")

    # Create a test cache instance
    cache = ContentCache(base_cache_dir="test_cache")

    # Test data
    test_content = b"This is a test file content for caching."
    test_filename = "test_file.txt"
    test_extension = "txt"
    test_transcription = "This is the transcribed text content."

    # Test 1: Save transcription cache
    print("\n1. Testing transcription cache save...")
    content_hash = cache.save_transcription_cache(
        test_content, test_transcription, test_filename, test_extension
    )
    print(f"Saved with content hash: {content_hash[:8]}...")

    # Test 2: Check cache exists
    print("\n2. Testing cache existence check...")
    has_cache = cache.has_transcription_cache(test_content)
    print(f"Cache exists: {has_cache}")

    # Test 3: Retrieve cached transcription
    print("\n3. Testing cache retrieval...")
    cached_data = cache.get_transcription_cache(test_content)
    if cached_data:
        print(f"Retrieved text: {cached_data['text'][:50]}...")
        print(f"Original filename: {cached_data['metadata'].get('original_filename')}")
        print(f"Cache hit: {cached_data['cache_info']['cache_hit']}")
    else:
        print("Failed to retrieve cached data!")

    # Test 4: Test with different content (should not find cache)
    print("\n4. Testing cache miss...")
    different_content = b"This is different content."
    has_different_cache = cache.has_transcription_cache(different_content)
    print(f"Different content has cache: {has_different_cache}")

    # Test 5: Cache statistics
    print("\n5. Testing cache statistics...")
    stats = cache.get_cache_stats()
    print(f"Total entries: {stats['total_entries']}")
    print(f"Transcription entries: {stats['transcription_entries']}")
    print(f"Total size: {stats['total_size_mb']:.2f} MB")

    # Test 6: Processed data cache
    print("\n6. Testing processed data cache...")
    test_processed_data = {
        "segments": [{"text": "Test segment", "position": 0}],
        "clusters": [{"cluster_id": 0, "heading": "Test Topic"}],
        "meta": {"total_words": 2},
    }

    processed_hash = cache.save_processed_cache(
        test_content, test_processed_data, test_filename
    )
    print(f"Saved processed data with hash: {processed_hash[:8]}...")

    # Retrieve processed cache
    cached_processed = cache.get_processed_cache(test_content)
    if cached_processed:
        print(
            f"Retrieved processed data with {len(cached_processed.get('segments', []))} segments"
        )
        print(
            f"Cache info: {cached_processed.get('cache_info', {}).get('content_hash', '')[:8]}..."
        )

    print("\n✅ All tests completed successfully!")

    # Cleanup
    import shutil

    shutil.rmtree("test_cache", ignore_errors=True)
    print("🧹 Test cache cleaned up.")


if __name__ == "__main__":
    test_cache_functionality()
