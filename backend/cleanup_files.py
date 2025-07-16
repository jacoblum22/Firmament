#!/usr/bin/env python3
"""
Manual cleanup script for StudyMate v2.
Safe, conservative file cleanup with multiple safeguards.

Usage:
    python cleanup_files.py --help                    # Show all options
    python cleanup_files.py --dry-run                 # Show what would be cleaned (default)
    python cleanup_files.py --for-real               # Actually clean files
    python cleanup_files.py --temp-only              # Only clean temp files
    python cleanup_files.py --status                 # Show directory status
"""

import argparse
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.file_cleanup import run_conservative_cleanup, SafeFileCleanup
import logging


def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def show_directory_status():
    """Show current directory sizes and file counts."""
    directories = ["uploads", "output", "processed", "temp_chunks", "rnnoise_output"]

    print("\n📁 Directory Status:")
    print("=" * 60)

    total_size = 0
    total_files = 0

    for dir_name in directories:
        dir_path = Path(dir_name)
        if dir_path.exists():
            files = list(dir_path.rglob("*"))
            file_count = len([f for f in files if f.is_file()])

            size_mb = 0
            for file_path in files:
                if file_path.is_file():
                    try:
                        size_mb += file_path.stat().st_size / (1024 * 1024)
                    except Exception:
                        pass

            total_size += size_mb
            total_files += file_count

            # Show oldest and newest files
            file_paths = [f for f in files if f.is_file()]
            if file_paths:
                import time

                current_time = time.time()
                oldest = min(file_paths, key=lambda f: f.stat().st_mtime)
                newest = max(file_paths, key=lambda f: f.stat().st_mtime)
                oldest_age = (current_time - oldest.stat().st_mtime) / 86400
                newest_age = (current_time - newest.stat().st_mtime) / 86400

                print(
                    f"{dir_name:15} | {file_count:5} files | {size_mb:8.1f}MB | "
                    f"oldest: {oldest_age:5.1f}d | newest: {newest_age:5.1f}d"
                )
            else:
                print(
                    f"{dir_name:15} | {file_count:5} files | {size_mb:8.1f}MB | (empty)"
                )
        else:
            print(f"{dir_name:15} | (doesn't exist)")

    print("-" * 60)
    print(f"{'TOTAL':15} | {total_files:5} files | {total_size:8.1f}MB")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Conservative file cleanup for StudyMate v2",
        epilog="By default, runs in dry-run mode to show what would be cleaned.",
    )

    # Action options
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Show what would be deleted without actually deleting (default)",
    )
    parser.add_argument(
        "--for-real",
        action="store_true",
        help="Actually delete files (overrides --dry-run)",
    )
    parser.add_argument(
        "--temp-only",
        action="store_true",
        help="Only clean temporary files (safest option)",
    )
    parser.add_argument(
        "--status", action="store_true", help="Show directory status and exit"
    )

    # Configuration options
    parser.add_argument(
        "--uploads-max-age",
        type=int,
        default=30,
        help="Max age for uploaded files in days (default: 30)",
    )
    parser.add_argument(
        "--output-max-age",
        type=int,
        default=90,
        help="Max age for output files in days (default: 90)",
    )
    parser.add_argument(
        "--processed-max-age",
        type=int,
        default=180,
        help="Max age for processed files in days (default: 180)",
    )
    parser.add_argument(
        "--temp-max-age",
        type=int,
        default=24,
        help="Max age for temp files in hours (default: 24)",
    )
    parser.add_argument(
        "--min-keep",
        type=int,
        default=5,
        help="Minimum files to always keep (default: 5)",
    )

    # Utility options
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    setup_logging(args.verbose)

    # Show status and exit if requested
    if args.status:
        show_directory_status()
        return 0

    # Determine if we're doing a dry run
    dry_run = args.dry_run and not args.for_real

    # Custom settings based on arguments
    custom_settings = {
        "uploads_max_age_days": args.uploads_max_age,
        "output_max_age_days": args.output_max_age,
        "processed_max_age_days": args.processed_max_age,
        "temp_chunks_max_age_hours": args.temp_max_age,
        "min_files_to_keep": args.min_keep,
        "dry_run": dry_run,
    }

    print("\n🧹 StudyMate File Cleanup")
    print("=" * 50)
    print(
        f"Mode: {'DRY RUN (no files will be deleted)' if dry_run else 'REAL CLEANUP (files will be deleted)'}"
    )
    print(
        f"Scope: {'Temporary files only' if args.temp_only else 'All configured directories'}"
    )
    print()

    if not dry_run:
        response = input(
            "⚠️  This will actually delete files. Continue? (yes/no): "
        ).lower()
        if response not in ["yes", "y"]:
            print("Cleanup cancelled.")
            return 0

    try:
        if args.temp_only:
            # Only clean temporary files (safest)
            cleanup = SafeFileCleanup(custom_settings)
            results = cleanup.cleanup_temp_chunks()
            print("\n📊 Temp Cleanup Results:")
            print(f"   Deleted: {results['deleted']} files")
            print(f"   Skipped: {results['skipped']} files")
            print(f"   Errors: {results['errors']} files")
            print(f"   Space freed: {results['size_freed_mb']:.1f}MB")
        else:
            # Full cleanup
            results = run_conservative_cleanup(
                dry_run=dry_run, settings=custom_settings
            )

            print("\n📊 Full Cleanup Results:")
            print(f"   Total deleted: {results['total_deleted']} files")
            print(f"   Total space freed: {results['total_size_freed_mb']:.1f}MB")

            if args.verbose:
                print("\n📁 Detailed Results:")
                for category, data in results.items():
                    if isinstance(data, dict) and "deleted" in data:
                        print(
                            f"   {category}: {data['deleted']} files, {data['size_freed_mb']:.1f}MB"
                        )

        if dry_run:
            print("\n💡 To actually delete files, run with --for-real")

        print("\n✅ Cleanup completed successfully!")
        return 0

    except Exception as e:
        print(f"\n❌ Cleanup failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
