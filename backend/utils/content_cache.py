"""
Content-based caching system for StudyMate v2.
Uses SHA256 content hashing to identify identical files regardless of filename.
"""

import hashlib
import json
from pathlib import Path
from typing import Dict, Optional, Any, Tuple
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ContentCache:
    """
    Content-based caching system that uses file content hashes to avoid reprocessing.

    Cache structure:
    cache/
    ├── transcriptions/
    │   ├── [hash].txt       # Raw transcription text
    │   └── [hash].meta.json # Metadata (filename, timestamp, etc.)
    ├── processed/
    │   ├── [hash].json      # Processed data (segments, clusters, etc.)
    │   └── [hash].meta.json # Metadata
    └── index.json           # Cache index for quick lookups
    """

    def __init__(self, base_cache_dir: str = "cache"):
        self.base_dir = Path(base_cache_dir)
        self.transcription_dir = self.base_dir / "transcriptions"
        self.processed_dir = self.base_dir / "processed"
        self.index_file = self.base_dir / "index.json"

        # Create directories
        self.base_dir.mkdir(exist_ok=True)
        self.transcription_dir.mkdir(exist_ok=True)
        self.processed_dir.mkdir(exist_ok=True)

        # Load or create cache index
        self.index = self._load_index()

    def _load_index(self) -> Dict[str, Any]:
        """Load cache index from disk."""
        if self.index_file.exists():
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load cache index: {e}. Creating new index.")

        return {
            "created": datetime.now().isoformat(),
            "last_cleanup": datetime.now().isoformat(),
            "entries": {},
        }

    def _save_index(self) -> bool:
        """Save cache index to disk."""
        try:
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(self.index, f, indent=2)
            return True
        except IOError as e:
            logger.error(f"Failed to save cache index: {e}")
            return False

    def calculate_content_hash(self, file_content: bytes) -> str:
        """Calculate SHA256 hash of file content."""
        return hashlib.sha256(file_content).hexdigest()

    def _get_cache_paths(self, content_hash: str, cache_type: str) -> Tuple[Path, Path]:
        """Get cache file and metadata paths for a given hash and type."""
        if cache_type == "transcription":
            cache_dir = self.transcription_dir
            cache_file = cache_dir / f"{content_hash}.txt"
            meta_file = cache_dir / f"{content_hash}.meta.json"
        elif cache_type == "processed":
            cache_dir = self.processed_dir
            cache_file = cache_dir / f"{content_hash}.json"
            meta_file = cache_dir / f"{content_hash}.meta.json"
        else:
            raise ValueError(f"Invalid cache type: {cache_type}")

        logger.debug(
            f"Cache paths for {content_hash[:8]}: file={cache_file}, meta={meta_file}"
        )
        return cache_file, meta_file

    def has_transcription_cache(self, file_content: bytes) -> bool:
        """Check if transcription cache exists for the given file content."""
        content_hash = self.calculate_content_hash(file_content)
        cache_file, _ = self._get_cache_paths(content_hash, "transcription")
        return cache_file.exists()

    def get_transcription_cache(self, file_content: bytes) -> Optional[Dict[str, Any]]:
        """
        Get cached transcription data for the given file content.

        Returns:
            Dict containing 'text', 'metadata', and 'cache_info' if found, None otherwise.
        """
        content_hash = self.calculate_content_hash(file_content)
        cache_file, meta_file = self._get_cache_paths(content_hash, "transcription")

        if not cache_file.exists():
            logger.debug(f"Cache file does not exist: {cache_file}")
            return None

        try:
            # Load transcription text
            with open(cache_file, "r", encoding="utf-8") as f:
                text = f.read()

            # Load metadata if it exists
            metadata = {}
            if meta_file.exists():
                with open(meta_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)

            # Update access time in index
            if content_hash in self.index.get("entries", {}):
                self.index["entries"][content_hash][
                    "last_accessed"
                ] = datetime.now().isoformat()
                self._save_index()

            cache_info = {
                "content_hash": content_hash,
                "cached_at": metadata.get("cached_at"),
                "original_filename": metadata.get("original_filename"),
                "file_size": metadata.get("file_size"),
                "cache_hit": True,
            }

            logger.info(f"Cache hit for transcription: {content_hash[:8]}...")

            return {"text": text, "metadata": metadata, "cache_info": cache_info}

        except (IOError, json.JSONDecodeError) as e:
            logger.error(
                f"Failed to load transcription cache for {content_hash[:8]}: {e}"
            )
            return None

    def save_transcription_cache(
        self,
        file_content: bytes,
        text: str,
        original_filename: str,
        file_extension: str,
    ) -> str:
        """
        Save transcription text to cache.

        Returns:
            Content hash of the cached file.
        """
        content_hash = self.calculate_content_hash(file_content)
        cache_file, meta_file = self._get_cache_paths(content_hash, "transcription")

        try:
            # Save transcription text
            with open(cache_file, "w", encoding="utf-8") as f:
                f.write(text)

            # Save metadata
            metadata = {
                "content_hash": content_hash,
                "original_filename": original_filename,
                "file_extension": file_extension,
                "file_size": len(file_content),
                "cached_at": datetime.now().isoformat(),
                "last_accessed": datetime.now().isoformat(),
                "cache_type": "transcription",
            }

            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)

            # Update index
            self.index["entries"][content_hash] = {
                "type": "transcription",
                "cached_at": metadata["cached_at"],
                "last_accessed": metadata["last_accessed"],
                "original_filename": original_filename,
                "file_size": len(file_content),
                "cache_file": str(cache_file.relative_to(self.base_dir)),
                "meta_file": str(meta_file.relative_to(self.base_dir)),
            }
            self._save_index()

            logger.info(
                f"Cached transcription for {content_hash[:8]}... (original: {original_filename})"
            )

            return content_hash

        except IOError as e:
            logger.error(
                f"Failed to save transcription cache for {content_hash[:8]}: {e}"
            )
            raise

    def has_processed_cache(self, file_content: bytes) -> bool:
        """Check if processed data cache exists for the given file content."""
        content_hash = self.calculate_content_hash(file_content)
        cache_file, _ = self._get_cache_paths(content_hash, "processed")
        return cache_file.exists()

    def get_processed_cache(self, file_content: bytes) -> Optional[Dict[str, Any]]:
        """
        Get cached processed data for the given file content.

        Returns:
            Dict containing processed data if found, None otherwise.
        """
        content_hash = self.calculate_content_hash(file_content)
        cache_file, meta_file = self._get_cache_paths(content_hash, "processed")

        if not cache_file.exists():
            logger.debug(f"Cache file does not exist: {cache_file}")
            return None

        try:
            # Load processed data
            with open(cache_file, "r", encoding="utf-8") as f:
                processed_data = json.load(f)

            # Load metadata if it exists
            metadata = {}
            if meta_file.exists():
                with open(meta_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)

            # Update access time in index
            if content_hash in self.index.get("entries", {}):
                self.index["entries"][content_hash][
                    "last_accessed"
                ] = datetime.now().isoformat()
                self._save_index()

            # Add cache info to processed data
            processed_data["cache_info"] = {
                "content_hash": content_hash,
                "cached_at": metadata.get("cached_at"),
                "original_filename": metadata.get("original_filename"),
                "cache_hit": True,
            }

            logger.info(f"Cache hit for processed data: {content_hash[:8]}...")

            return processed_data

        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load processed cache for {content_hash[:8]}: {e}")
            return None

    def save_processed_cache(
        self,
        file_content: bytes,
        processed_data: Dict[str, Any],
        original_filename: str,
    ) -> str:
        """
        Save processed data to cache.

        Returns:
            Content hash of the cached file.
        """
        content_hash = self.calculate_content_hash(file_content)
        cache_file, meta_file = self._get_cache_paths(content_hash, "processed")

        try:
            # Remove cache_info from data before saving to avoid recursion
            data_to_save = {
                k: v for k, v in processed_data.items() if k != "cache_info"
            }

            # Save processed data
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, indent=2)

            # Save metadata
            metadata = {
                "content_hash": content_hash,
                "original_filename": original_filename,
                "file_size": len(file_content),
                "cached_at": datetime.now().isoformat(),
                "last_accessed": datetime.now().isoformat(),
                "cache_type": "processed",
            }

            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)

            # Update index
            self.index["entries"][content_hash] = {
                "type": "processed",
                "cached_at": metadata["cached_at"],
                "last_accessed": metadata["last_accessed"],
                "original_filename": original_filename,
                "file_size": len(file_content),
                "cache_file": str(cache_file.relative_to(self.base_dir)),
                "meta_file": str(meta_file.relative_to(self.base_dir)),
            }
            self._save_index()

            logger.info(
                f"Cached processed data for {content_hash[:8]}... (original: {original_filename})"
            )

            return content_hash

        except IOError as e:
            logger.error(f"Failed to save processed cache for {content_hash[:8]}: {e}")
            raise

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        entries = self.index.get("entries", {})
        transcription_count = sum(
            1 for entry in entries.values() if entry.get("type") == "transcription"
        )
        processed_count = sum(
            1 for entry in entries.values() if entry.get("type") == "processed"
        )

        total_size = 0
        for entry in entries.values():
            cache_file = self.base_dir / entry.get("cache_file", "")
            if cache_file.exists():
                total_size += cache_file.stat().st_size

        return {
            "total_entries": len(entries),
            "transcription_entries": transcription_count,
            "processed_entries": processed_count,
            "total_size_mb": total_size / (1024 * 1024),
            "cache_directory": str(self.base_dir),
            "created": self.index.get("created"),
            "last_cleanup": self.index.get("last_cleanup"),
        }

    def cleanup_old_entries(self, max_age_days: int = 30) -> Dict[str, int]:
        """
        Clean up cache entries older than max_age_days.

        Returns:
            Dict with cleanup statistics.
        """
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        entries = self.index.get("entries", {})

        deleted_count = 0
        errors = 0
        freed_size = 0

        entries_to_delete = []

        for content_hash, entry in entries.items():
            try:
                cached_at = datetime.fromisoformat(entry.get("cached_at", ""))
                if cached_at < cutoff_date:
                    # Calculate freed size before deletion
                    cache_file = self.base_dir / entry.get("cache_file", "")
                    meta_file = self.base_dir / entry.get("meta_file", "")

                    if cache_file.exists():
                        freed_size += cache_file.stat().st_size
                        cache_file.unlink()

                    if meta_file.exists():
                        freed_size += meta_file.stat().st_size
                        meta_file.unlink()

                    entries_to_delete.append(content_hash)
                    deleted_count += 1

            except (ValueError, OSError) as e:
                logger.error(f"Error cleaning up cache entry {content_hash[:8]}: {e}")
                errors += 1

        # Remove deleted entries from index
        for content_hash in entries_to_delete:
            del entries[content_hash]

        # Update cleanup timestamp
        self.index["last_cleanup"] = datetime.now().isoformat()
        self._save_index()

        stats = {
            "deleted_entries": deleted_count,
            "freed_size_mb": freed_size / (1024 * 1024),
            "errors": errors,
        }

        if deleted_count > 0:
            logger.info(
                f"Cache cleanup: deleted {deleted_count} entries, freed {stats['freed_size_mb']:.2f} MB"
            )

        return stats


# Global cache instance
_cache_instance = None


def get_content_cache() -> ContentCache:
    """Get the global content cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = ContentCache()
    return _cache_instance
