#!/usr/bin/env python3
"""
Test script for the content-based caching system with proper assertions.
"""

import os
import sys
import pytest
import shutil

# Add the backend directory to the Python path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
sys.path.insert(0, backend_dir)

from utils.content_cache import ContentCache


def test_transcription_cache():
    """Test transcription caching functionality with assertions."""
    test_cache_dir = "test_cache_transcription"
    if os.path.exists(test_cache_dir):
        shutil.rmtree(test_cache_dir)

    try:
        cache = ContentCache(base_cache_dir=test_cache_dir)

        # Test data
        test_content = b"This is some test audio content for caching."
        test_filename = "test_file.txt"
        test_extension = "txt"
        test_transcription = "This is the transcribed text content."

        # Test save transcription cache
        content_hash = cache.save_transcription_cache(
            test_content, test_transcription, test_filename, test_extension
        )
        assert content_hash is not None, "Content hash should not be None"
        assert isinstance(content_hash, str), "Content hash should be a string"
        assert len(content_hash) > 0, "Content hash should not be empty"

        # Test cache exists
        has_cache = cache.has_transcription_cache(test_content)
        assert has_cache is True, "Cache should exist for the test content"

        # Test retrieve cached transcription
        cached_data = cache.get_transcription_cache(test_content)
        assert cached_data is not None, "Cached data should not be None"
        assert (
            cached_data["text"] == test_transcription
        ), "Cached text should match original"
        assert (
            cached_data["metadata"]["original_filename"] == test_filename
        ), "Filename should match"
        assert (
            cached_data["cache_info"]["cache_hit"] is True
        ), "Cache hit should be True"
        assert (
            "content_hash" in cached_data["cache_info"]
        ), "Content hash should be in cache info"

        # Test cache miss with different content
        different_content = b"This is different content."
        has_different_cache = cache.has_transcription_cache(different_content)
        assert has_different_cache is False, "Different content should not have cache"

    finally:
        # Cleanup
        shutil.rmtree(test_cache_dir, ignore_errors=True)


def test_processed_cache():
    """Test processed data caching functionality with assertions."""
    test_cache_dir = "test_cache_processed"
    if os.path.exists(test_cache_dir):
        shutil.rmtree(test_cache_dir)

    try:
        cache = ContentCache(base_cache_dir=test_cache_dir)

        # Test data
        test_content = b"This is some test content for processed caching."
        test_filename = "test_processed.txt"
        test_processed_data = {
            "segments": [{"text": "Test segment", "position": 0}],
            "clusters": [{"cluster_id": 0, "heading": "Test Topic"}],
            "meta": {"total_words": 2},
        }

        # Test save processed cache
        processed_hash = cache.save_processed_cache(
            test_content, test_processed_data, test_filename
        )
        assert processed_hash is not None, "Processed hash should not be None"
        assert isinstance(processed_hash, str), "Processed hash should be a string"

        # Test retrieve processed cache
        cached_processed = cache.get_processed_cache(test_content)
        assert cached_processed is not None, "Cached processed data should not be None"
        assert "segments" in cached_processed, "Cached data should include segments"
        assert len(cached_processed["segments"]) == 1, "Should have one segment"
        assert (
            cached_processed["segments"][0]["text"] == "Test segment"
        ), "Segment text should match"
        assert "cache_info" in cached_processed, "Should include cache info"

    finally:
        # Cleanup
        shutil.rmtree(test_cache_dir, ignore_errors=True)


def test_cache_statistics():
    """Test cache statistics functionality."""
    test_cache_dir = "test_cache_stats"
    if os.path.exists(test_cache_dir):
        shutil.rmtree(test_cache_dir)

    try:
        cache = ContentCache(base_cache_dir=test_cache_dir)

        # Add some test data
        test_content = b"Test content for stats"
        cache.save_transcription_cache(
            test_content, "Test transcription", "test.txt", "txt"
        )

        # Test statistics
        stats = cache.get_cache_stats()
        assert isinstance(stats, dict), "Cache stats should be a dictionary"
        assert "total_entries" in stats, "Stats should include total_entries"
        assert (
            "transcription_entries" in stats
        ), "Stats should include transcription_entries"
        assert "total_size_mb" in stats, "Stats should include total_size_mb"
        assert stats["total_entries"] >= 1, "Should have at least one cache entry"

    finally:
        # Cleanup
        shutil.rmtree(test_cache_dir, ignore_errors=True)


def test_cache_error_handling():
    """Test cache error handling with invalid inputs."""
    test_cache_dir = "test_cache_errors"
    if os.path.exists(test_cache_dir):
        shutil.rmtree(test_cache_dir)

    try:
        cache = ContentCache(base_cache_dir=test_cache_dir)

        # Test with empty data - should handle gracefully
        try:
            result = cache.save_transcription_cache(b"", "", "", "")
            # If it doesn't raise an exception, it should handle gracefully
            assert result is None or isinstance(
                result, str
            ), "Should handle invalid input gracefully"
        except (ValueError, TypeError):
            # It's acceptable for the cache to raise appropriate exceptions for invalid input
            pass

        # Test retrieving non-existent cache
        non_existent_result = cache.get_transcription_cache(b"non-existent content")
        assert non_existent_result is None, "Non-existent cache should return None"

    finally:
        # Cleanup
        shutil.rmtree(test_cache_dir, ignore_errors=True)


if __name__ == "__main__":
    # Run all tests
    test_transcription_cache()
    test_processed_cache()
    test_cache_statistics()
    test_cache_error_handling()
    print("✅ All cache tests completed successfully!")
