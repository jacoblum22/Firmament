import unittest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path
from utils.content_cache import ContentCache
import os
import json
from datetime import datetime, timedelta


class TestContentCache(unittest.TestCase):

    def setUp(self):
        # Mock the base directory to avoid actual file operations
        self.mock_base_dir = "mock_cache"
        self.cache = ContentCache(base_cache_dir=self.mock_base_dir)

    def tearDown(self):
        # Clean up the mock directory
        if os.path.exists(self.mock_base_dir):
            for root, dirs, files in os.walk(self.mock_base_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(self.mock_base_dir)

    def test_save_and_get_transcription_cache(self):
        file_content = b"This is a test file content."
        text = "This is the transcribed text."
        filename = "test_file.txt"
        extension = "txt"

        # Save transcription cache
        content_hash = self.cache.save_transcription_cache(
            file_content, text, filename, extension
        )

        # Verify cache file exists
        cache_file, _ = self.cache._get_cache_paths(content_hash, "transcription")
        self.assertTrue(cache_file.exists(), "Cache file does not exist after saving.")

        # Retrieve transcription cache
        cached_data = self.cache.get_transcription_cache(file_content)

        self.assertIsNotNone(cached_data, "Cached data is None.")
        if cached_data is not None:
            self.assertEqual(cached_data["text"], text)
        if cached_data is not None:
            self.assertEqual(cached_data["cache_info"]["content_hash"], content_hash)

    def test_save_and_get_processed_cache(self):
        file_content = b"This is another test file content."
        processed_data = {
            "segments": ["Segment 1", "Segment 2"],
            "meta": {"info": "test"},
        }
        filename = "processed_file.json"

        # Save processed cache
        content_hash = self.cache.save_processed_cache(
            file_content, processed_data, filename
        )

        # Verify cache file exists
        cache_file, _ = self.cache._get_cache_paths(content_hash, "processed")
        self.assertTrue(cache_file.exists(), "Cache file does not exist after saving.")

        # Retrieve processed cache
        cached_data = self.cache.get_processed_cache(file_content)

        self.assertIsNotNone(cached_data, "Cached data is None.")
        if cached_data is not None:
            self.assertEqual(cached_data["segments"], processed_data["segments"])
            self.assertEqual(cached_data["cache_info"]["content_hash"], content_hash)

    def test_has_transcription_cache(self):
        file_content = b"This is a test file content."
        text = "This is the transcribed text."
        filename = "test_file.txt"
        extension = "txt"

        # Initially, cache should not exist
        self.assertFalse(self.cache.has_transcription_cache(file_content))

        # Save transcription cache
        self.cache.save_transcription_cache(file_content, text, filename, extension)

        # Now, cache should exist
        self.assertTrue(self.cache.has_transcription_cache(file_content))

    def test_cleanup_old_entries(self):
        file_content = b"Old file content."
        text = "Old transcribed text."
        filename = "old_file.txt"
        extension = "txt"

        # Save transcription cache
        self.cache.save_transcription_cache(file_content, text, filename, extension)

        # Mock the index to simulate an old entry
        old_date = (datetime.now() - timedelta(days=31)).isoformat()
        content_hash = self.cache._calculate_content_hash(file_content)
        self.cache.index["entries"][content_hash]["cached_at"] = old_date
        self.cache._save_index()

        # Perform cleanup
        stats = self.cache.cleanup_old_entries(max_age_days=30)

        self.assertEqual(stats["deleted_entries"], 1)
        self.assertGreater(stats["freed_size_mb"], 0)


if __name__ == "__main__":
    unittest.main()
