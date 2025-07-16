"""
Background cleanup service for StudyMate v2.
Provides optional periodic cleanup without being intrusive.
"""

import threading
import time
import logging
from typing import Optional
import os
from .file_cleanup import run_conservative_cleanup

logger = logging.getLogger(__name__)


class CleanupService:
    """
    Optional background service for periodic file cleanup.
    Designed to be non-intrusive and easily disabled.
    """

    def __init__(self):
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

        # Get settings from environment variables with conservative defaults
        self.enabled = os.getenv("CLEANUP_ENABLED", "false").lower() == "true"
        self.interval_hours = int(
            os.getenv("CLEANUP_INTERVAL_HOURS", "24")
        )  # Once per day
        self.startup_delay_minutes = int(
            os.getenv("CLEANUP_STARTUP_DELAY_MINUTES", "10")
        )  # Wait 10 min after startup

        # Override settings for more conservative cleanup
        self.cleanup_settings = {
            "temp_chunks_max_age_hours": int(
                os.getenv("CLEANUP_TEMP_MAX_AGE_HOURS", "24")
            ),
            "uploads_max_age_days": int(
                os.getenv("CLEANUP_UPLOADS_MAX_AGE_DAYS", "30")
            ),
            "output_max_age_days": int(os.getenv("CLEANUP_OUTPUT_MAX_AGE_DAYS", "90")),
            "processed_max_age_days": int(
                os.getenv("CLEANUP_PROCESSED_MAX_AGE_DAYS", "180")
            ),
            "uploads_max_size_mb": int(
                os.getenv("CLEANUP_UPLOADS_MAX_SIZE_MB", "5000")
            ),
            "output_max_size_mb": int(os.getenv("CLEANUP_OUTPUT_MAX_SIZE_MB", "2000")),
            "processed_max_size_mb": int(
                os.getenv("CLEANUP_PROCESSED_MAX_SIZE_MB", "1000")
            ),
            "min_files_to_keep": int(os.getenv("CLEANUP_MIN_FILES_TO_KEEP", "5")),
            "enable_cleanup": True,
            "dry_run": False,
        }

    def start(self):
        """Start the cleanup service if enabled."""
        if not self.enabled:
            logger.info("File cleanup service disabled (CLEANUP_ENABLED=false)")
            return

        if self.running:
            logger.warning("Cleanup service already running")
            return

        logger.info(
            f"Starting file cleanup service (interval: {self.interval_hours}h, "
            f"startup delay: {self.startup_delay_minutes}m)"
        )

        self.running = True
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the cleanup service."""
        if not self.running:
            return

        logger.info("Stopping file cleanup service...")
        self.running = False
        self.stop_event.set()

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)

        logger.info("File cleanup service stopped")

    def _cleanup_loop(self):
        """Main cleanup loop running in background thread."""
        try:
            # Wait before first cleanup to let the system settle
            startup_delay_seconds = self.startup_delay_minutes * 60
            logger.info(
                f"Cleanup service waiting {self.startup_delay_minutes} minutes before first run..."
            )

            if self.stop_event.wait(startup_delay_seconds):
                return  # Service was stopped during startup delay

            # Main cleanup loop
            while self.running and not self.stop_event.is_set():
                try:
                    logger.info("Running periodic file cleanup...")
                    results = run_conservative_cleanup(
                        dry_run=False, settings=self.cleanup_settings
                    )

                    if results.get("total_deleted", 0) > 0:
                        logger.info(
                            f"Cleanup completed: deleted {results['total_deleted']} files, "
                            f"freed {results['total_size_freed_mb']:.1f}MB"
                        )
                    else:
                        logger.debug("Cleanup completed: no files deleted")

                except Exception as e:
                    logger.error(f"Error during periodic cleanup: {e}")

                # Wait for next cleanup cycle
                interval_seconds = self.interval_hours * 3600
                if self.stop_event.wait(interval_seconds):
                    break  # Service was stopped during wait

        except Exception as e:
            logger.error(f"Cleanup service error: {e}")
        finally:
            self.running = False

    def run_manual_cleanup(self, dry_run: bool = False) -> dict:
        """Run cleanup manually (can be called from API endpoint)."""
        logger.info(f"Running manual cleanup (dry_run={dry_run})")
        return run_conservative_cleanup(dry_run=dry_run, settings=self.cleanup_settings)

    def get_status(self) -> dict:
        """Get current service status."""
        return {
            "enabled": self.enabled,
            "running": self.running,
            "interval_hours": self.interval_hours,
            "startup_delay_minutes": self.startup_delay_minutes,
            "settings": self.cleanup_settings,
        }


# Global service instance
_cleanup_service: Optional[CleanupService] = None


def get_cleanup_service() -> CleanupService:
    """Get the global cleanup service instance."""
    global _cleanup_service
    if _cleanup_service is None:
        _cleanup_service = CleanupService()
    return _cleanup_service


def start_cleanup_service():
    """Start the cleanup service (called from main.py)."""
    service = get_cleanup_service()
    service.start()


def stop_cleanup_service():
    """Stop the cleanup service (called on shutdown)."""
    service = get_cleanup_service()
    service.stop()
