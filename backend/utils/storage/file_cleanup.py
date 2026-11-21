"""
Conservative file cleanup utilities for StudyMate v2.
Focuses on safety and configurable cleanup with multiple safeguards.
"""

import time
from pathlib import Path
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# Conservative default settings - very gentle cleanup
DEFAULT_SETTINGS = {
    # Age limits (in days) - conservative defaults
    "temp_chunks_max_age_hours": 24,  # Temp chunks older than 1 day
    "uploads_max_age_days": 30,  # Uploaded files older than 30 days
    "output_max_age_days": 90,  # Output files older than 90 days
    "processed_max_age_days": 180,  # Processed files older than 6 months
    # Size limits (in MB) - generous defaults
    "uploads_max_size_mb": 5000,  # 5GB for uploads directory
    "output_max_size_mb": 2000,  # 2GB for output directory
    "processed_max_size_mb": 1000,  # 1GB for processed directory
    # Safety settings
    "min_files_to_keep": 5,  # Always keep at least 5 newest files
    "dry_run": False,  # Set to True to see what would be cleaned without actually doing it
    "enable_cleanup": True,  # Master switch to disable all cleanup
}


class SafeFileCleanup:
    """
    Conservative file cleanup with multiple safety mechanisms.
    """

    def __init__(self, settings: Optional[dict] = None):
        self.settings = {**DEFAULT_SETTINGS, **(settings or {})}
        self.deleted_files = []
        self.skipped_files = []

    def is_safe_to_delete(
        self, file_path: Path, max_age_days: float
    ) -> Tuple[bool, str]:
        """
        Determine if a file is safe to delete with multiple safety checks.
        Returns (is_safe, reason)
        """
        try:
            # Check if file exists
            if not file_path.exists():
                return False, "File doesn't exist"

            # Check file age
            file_age = time.time() - file_path.stat().st_mtime
            max_age_seconds = max_age_days * 24 * 3600

            if file_age < max_age_seconds:
                return False, f"File too recent ({file_age/3600:.1f} hours old)"

            # Safety check: Never delete files newer than 1 hour (in case of clock issues)
            if file_age < 3600:
                return False, "Safety: File newer than 1 hour"

            # Safety check: Skip very large files (might be important)
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > 1000:  # 1GB
                return False, f"Safety: File too large ({file_size_mb:.1f}MB)"

            # Safety check: Skip files with suspicious patterns that might be user data
            suspicious_patterns = [
                "backup",
                "important",
                "keep",
                "save",
                "final",
                "presentation",
                "lecture",
                "meeting",
                "interview",
            ]
            filename_lower = file_path.name.lower()
            for pattern in suspicious_patterns:
                if pattern in filename_lower:
                    return False, f"Safety: Filename contains '{pattern}'"

            return True, "Safe to delete"

        except Exception as e:
            return False, f"Error checking file: {e}"

    def get_files_by_age(
        self, directory: Path, pattern: str = "*"
    ) -> List[Tuple[Path, float]]:
        """Get files sorted by age (oldest first) with their age in days."""
        if not directory.exists():
            return []

        files_with_age = []
        try:
            for file_path in directory.glob(pattern):
                if file_path.is_file():
                    age_seconds = time.time() - file_path.stat().st_mtime
                    age_days = age_seconds / (24 * 3600)
                    files_with_age.append((file_path, age_days))
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {e}")

        return sorted(files_with_age, key=lambda x: x[1], reverse=True)  # Oldest first

    def cleanup_temp_chunks(self) -> dict:
        """Clean up temporary chunk files (most aggressive since these are truly temporary)."""
        results = {"deleted": 0, "skipped": 0, "errors": 0, "size_freed_mb": 0.0}

        if not self.settings["enable_cleanup"]:
            return results

        temp_dir = Path("temp_chunks")
        if not temp_dir.exists():
            return results

        max_age_hours = self.settings["temp_chunks_max_age_hours"]
        max_age_days = max_age_hours / 24

        logger.info(f"Cleaning temp chunks older than {max_age_hours} hours")

        files_with_age = self.get_files_by_age(temp_dir, "*.wav")

        for file_path, age_days in files_with_age:
            is_safe, reason = self.is_safe_to_delete(file_path, max_age_days)

            if is_safe:
                try:
                    file_size_mb = file_path.stat().st_size / (1024 * 1024)
                    if not self.settings["dry_run"]:
                        file_path.unlink()
                        logger.info(f"Deleted temp file: {file_path}")
                        self.deleted_files.append(str(file_path))
                    else:
                        logger.info(f"DRY RUN: Would delete temp file: {file_path}")

                    results["deleted"] += 1
                    results["size_freed_mb"] += file_size_mb

                except Exception as e:
                    logger.error(f"Error deleting {file_path}: {e}")
                    results["errors"] += 1
            else:
                logger.debug(f"Skipped {file_path}: {reason}")
                self.skipped_files.append((str(file_path), reason))
                results["skipped"] += 1

        return results

    def cleanup_by_size_limit(
        self, directory: Path, max_size_mb: int, min_keep: int = 5
    ) -> dict:
        """Remove oldest files if directory exceeds size limit, but keep minimum number of files."""
        results = {"deleted": 0, "skipped": 0, "errors": 0, "size_freed_mb": 0.0}

        if not self.settings["enable_cleanup"] or not directory.exists():
            return results

        # Calculate current directory size
        total_size_mb = 0
        all_files = []

        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    size_mb = file_path.stat().st_size / (1024 * 1024)
                    age_seconds = time.time() - file_path.stat().st_mtime
                    age_days = age_seconds / (24 * 3600)
                    total_size_mb += size_mb
                    all_files.append((file_path, age_days, size_mb))
        except Exception as e:
            logger.error(f"Error scanning {directory}: {e}")
            return results

        if total_size_mb <= max_size_mb:
            logger.info(
                f"Directory {directory} is under size limit ({total_size_mb:.1f}MB <= {max_size_mb}MB)"
            )
            return results

        logger.info(
            f"Directory {directory} exceeds size limit ({total_size_mb:.1f}MB > {max_size_mb}MB)"
        )

        # Sort by age (oldest first) and only consider files older than minimum age
        old_files = [
            (f, age, size) for f, age, size in all_files if age > 1
        ]  # At least 1 day old
        old_files.sort(key=lambda x: x[1], reverse=True)  # Oldest first

        # Keep minimum number of files regardless of size
        files_to_consider = old_files[min_keep:] if len(old_files) > min_keep else []

        current_size = total_size_mb
        target_size = (
            max_size_mb * 0.8
        )  # Clean to 80% of limit to avoid immediate re-triggering

        for file_path, age_days, size_mb in files_to_consider:
            if current_size <= target_size:
                break

            # Additional safety check for size-based cleanup
            if age_days < 7:  # Don't delete files newer than 1 week for size cleanup
                logger.debug(
                    f"Skipped {file_path}: Too recent for size cleanup ({age_days:.1f} days)"
                )
                results["skipped"] += 1
                continue

            try:
                if not self.settings["dry_run"]:
                    file_path.unlink()
                    logger.info(
                        f"Deleted for size limit: {file_path} ({size_mb:.1f}MB)"
                    )
                    self.deleted_files.append(str(file_path))
                else:
                    logger.info(
                        f"DRY RUN: Would delete for size: {file_path} ({size_mb:.1f}MB)"
                    )

                results["deleted"] += 1
                results["size_freed_mb"] += size_mb
                current_size -= size_mb

            except Exception as e:
                logger.error(f"Error deleting {file_path}: {e}")
                results["errors"] += 1

        return results

    def cleanup_old_files_in_directory(
        self, directory: Path, max_age_days: int, pattern: str = "*"
    ) -> dict:
        """Clean up old files in a directory based on age."""
        results = {"deleted": 0, "skipped": 0, "errors": 0, "size_freed_mb": 0.0}

        if not self.settings["enable_cleanup"] or not directory.exists():
            return results

        logger.info(f"Cleaning files in {directory} older than {max_age_days} days")

        files_with_age = self.get_files_by_age(directory, pattern)

        # Always keep minimum number of files
        min_keep = self.settings["min_files_to_keep"]
        files_to_consider = (
            files_with_age[min_keep:] if len(files_with_age) > min_keep else []
        )

        for file_path, age_days in files_to_consider:
            is_safe, reason = self.is_safe_to_delete(file_path, max_age_days)

            if is_safe:
                try:
                    file_size_mb = file_path.stat().st_size / (1024 * 1024)
                    if not self.settings["dry_run"]:
                        file_path.unlink()
                        logger.info(
                            f"Deleted old file: {file_path} ({age_days:.1f} days old)"
                        )
                        self.deleted_files.append(str(file_path))
                    else:
                        logger.info(
                            f"DRY RUN: Would delete: {file_path} ({age_days:.1f} days old)"
                        )

                    results["deleted"] += 1
                    results["size_freed_mb"] += file_size_mb

                except Exception as e:
                    logger.error(f"Error deleting {file_path}: {e}")
                    results["errors"] += 1
            else:
                logger.debug(f"Skipped {file_path}: {reason}")
                self.skipped_files.append((str(file_path), reason))
                results["skipped"] += 1

        return results

    def run_full_cleanup(self) -> dict:
        """Run complete cleanup with all configured settings."""
        if not self.settings["enable_cleanup"]:
            logger.info("Cleanup disabled by configuration")
            return {
                "total_deleted": 0,
                "total_size_freed_mb": 0.0,
                "cleanup_disabled": True,
            }

        logger.info("Starting conservative file cleanup...")
        total_results = {"total_deleted": 0, "total_size_freed_mb": 0.0}

        # 1. Clean temp chunks (most aggressive)
        temp_results = self.cleanup_temp_chunks()
        total_results["temp_chunks"] = temp_results
        total_results["total_deleted"] += temp_results["deleted"]
        total_results["total_size_freed_mb"] += temp_results["size_freed_mb"]

        # 2. Clean old files by age (conservative)
        uploads_results = self.cleanup_old_files_in_directory(
            Path("uploads"), self.settings["uploads_max_age_days"]
        )
        total_results["uploads_age"] = uploads_results
        total_results["total_deleted"] += uploads_results["deleted"]
        total_results["total_size_freed_mb"] += uploads_results["size_freed_mb"]

        output_results = self.cleanup_old_files_in_directory(
            Path("output"), self.settings["output_max_age_days"]
        )
        total_results["output_age"] = output_results
        total_results["total_deleted"] += output_results["deleted"]
        total_results["total_size_freed_mb"] += output_results["size_freed_mb"]

        processed_results = self.cleanup_old_files_in_directory(
            Path("processed"), self.settings["processed_max_age_days"]
        )
        total_results["processed_age"] = processed_results
        total_results["total_deleted"] += processed_results["deleted"]
        total_results["total_size_freed_mb"] += processed_results["size_freed_mb"]

        # 3. Clean by size limits (if directories are too large)
        uploads_size_results = self.cleanup_by_size_limit(
            Path("uploads"), self.settings["uploads_max_size_mb"]
        )
        total_results["uploads_size"] = uploads_size_results
        total_results["total_deleted"] += uploads_size_results["deleted"]
        total_results["total_size_freed_mb"] += uploads_size_results["size_freed_mb"]

        output_size_results = self.cleanup_by_size_limit(
            Path("output"), self.settings["output_max_size_mb"]
        )
        total_results["output_size"] = output_size_results
        total_results["total_deleted"] += output_size_results["deleted"]
        total_results["total_size_freed_mb"] += output_size_results["size_freed_mb"]

        processed_size_results = self.cleanup_by_size_limit(
            Path("processed"), self.settings["processed_max_size_mb"]
        )
        total_results["processed_size"] = processed_size_results
        total_results["total_deleted"] += processed_size_results["deleted"]
        total_results["total_size_freed_mb"] += processed_size_results["size_freed_mb"]

        logger.info(
            f"Cleanup complete. Deleted {total_results['total_deleted']} files, "
            f"freed {total_results['total_size_freed_mb']:.1f}MB"
        )

        return total_results


def run_conservative_cleanup(
    dry_run: bool = False, settings: Optional[dict] = None
) -> dict:
    """
    Run a conservative cleanup with safe defaults.

    Args:
        dry_run: If True, only show what would be deleted without actually deleting
        settings: Custom settings to override defaults

    Returns:
        Dictionary with cleanup results
    """
    cleanup_settings = {**DEFAULT_SETTINGS, **(settings or {})}
    cleanup_settings["dry_run"] = dry_run

    cleanup = SafeFileCleanup(cleanup_settings)
    return cleanup.run_full_cleanup()


if __name__ == "__main__":
    # Run with dry_run=True by default for safety
    import argparse

    parser = argparse.ArgumentParser(
        description="Conservative file cleanup for StudyMate"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Show what would be deleted without actually deleting (default: True)",
    )
    parser.add_argument(
        "--for-real",
        action="store_true",
        help="Actually delete files (overrides --dry-run)",
    )
    parser.add_argument(
        "--temp-only", action="store_true", help="Only clean temporary files"
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    dry_run = args.dry_run and not args.for_real

    if args.temp_only:
        cleanup = SafeFileCleanup({"dry_run": dry_run})
        results = cleanup.cleanup_temp_chunks()
        print(f"Temp cleanup results: {results}")
    else:
        results = run_conservative_cleanup(dry_run=dry_run)
        print(f"Full cleanup results: {results}")
