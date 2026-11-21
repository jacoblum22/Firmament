import json
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException

from utils.storage.content_cache import get_content_cache
from utils.storage.secure_temp_files import SecureTempFile, get_memory_storage

from ..config import settings
from .constants import OUTPUT_DIR
from .upload import verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


def validate_max_age_days(max_age_days: int) -> int:
    """
    Validate max_age_days parameter for cache cleanup operations.
    """
    if max_age_days < 1:
        raise HTTPException(
            status_code=400,
            detail="max_age_days must be at least 1 day to prevent accidental deletion of recent cache entries.",
        )

    if max_age_days > 365:
        raise HTTPException(
            status_code=400,
            detail="max_age_days cannot exceed 365 days (1 year). Please use a smaller value.",
        )

    return max_age_days


def get_llm_api_key(
    x_openai_key: Optional[str] = Header(None, alias="X-OpenAI-Key"),
    x_llm_base_url: Optional[str] = Header(None, alias="X-LLM-Base-URL"),
    x_llm_model: Optional[str] = Header(None, alias="X-LLM-Model"),
) -> dict:
    """Extract user-provided LLM overrides from request headers."""
    return {
        "api_key": x_openai_key.strip() if x_openai_key else None,
        "base_url": x_llm_base_url.strip() if x_llm_base_url else None,
        "model": x_llm_model.strip() if x_llm_model else None,
    }


@router.get("/llm/status")
def llm_status():
    """Return LLM provider configuration and whether a user key is needed."""
    from utils.common.openai_client import get_llm_status

    return get_llm_status()


@router.get("/cleanup/status")
def get_cleanup_status():
    """Get cleanup service status (requires debug mode)"""
    if not settings.debug:
        raise HTTPException(status_code=404, detail="Endpoint not available")

    try:
        from utils.storage.cleanup_service import get_cleanup_service

        service = get_cleanup_service()
        return service.get_status()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting cleanup status: {e}"
        ) from e


@router.post("/cleanup/run")
def run_manual_cleanup(
    dry_run: bool = True, authenticated: bool = Depends(verify_api_key)
):
    """
    Run manual cleanup (requires debug mode, defaults to dry run)
    """
    if not settings.debug:
        raise HTTPException(status_code=404, detail="Endpoint not available")

    try:
        from utils.storage.cleanup_service import get_cleanup_service

        service = get_cleanup_service()
        results = service.run_manual_cleanup(dry_run=dry_run)
        return {
            "message": "Cleanup completed" if not dry_run else "Dry run completed",
            "dry_run": dry_run,
            "environment": settings.environment,
            "results": results,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error running cleanup: {e}"
        ) from e


@router.get("/cache/stats")
def get_cache_stats():
    """Get cache statistics and information"""
    try:
        cache = get_content_cache()
        stats = cache.get_cache_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get cache stats: {str(e)}"
        ) from e


@router.post("/cache/cleanup")
def cleanup_cache(
    data: Optional[dict] = None, authenticated: bool = Depends(verify_api_key)
):
    """
    Clean up old cache entries.
    """
    data = data or {}
    try:
        cache = get_content_cache()

        max_age_days = 30

        if "max_age_days" in data:
            try:
                max_age_days = int(data["max_age_days"])
                max_age_days = validate_max_age_days(max_age_days)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="max_age_days must be a valid integer."
                ) from None

        cleanup_stats = cache.cleanup_old_entries(max_age_days)

        return {
            "success": True,
            "message": f"Cache cleanup completed for entries older than {max_age_days} days",
            "max_age_days": max_age_days,
            "stats": cleanup_stats,
            "environment": settings.environment,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Cache cleanup failed: {str(e)}"
        ) from e


@router.get("/temp-storage/stats")
def get_temp_storage_stats():
    """Get statistics about temporary storage usage"""
    try:
        memory_storage = get_memory_storage()
        memory_stats = memory_storage.get_size_info()

        metadata_files = []
        pending_cleanup = []

        if os.path.exists(OUTPUT_DIR):
            for filename in os.listdir(OUTPUT_DIR):
                if filename.endswith("_metadata.json"):
                    metadata_path = os.path.join(OUTPUT_DIR, filename)
                    try:
                        with open(metadata_path, "r", encoding="utf-8") as f:
                            metadata = json.load(f)

                        metadata_files.append(
                            {
                                "filename": filename,
                                "storage_type": metadata.get(
                                    "temp_storage_type", "legacy"
                                ),
                                "created_at": metadata.get("created_at"),
                                "cleanup_completed": metadata.get(
                                    "cleanup_completed", False
                                ),
                                "has_temp_file": "temp_content_file" in metadata,
                            }
                        )

                        if (
                            not metadata.get("cleanup_completed", False)
                            and "temp_content_file" in metadata
                        ):
                            pending_cleanup.append(filename)

                    except Exception as e:
                        logger.warning(f"Failed to read metadata file {filename}: {e}")

        return {
            "memory_storage": memory_stats,
            "metadata_files_count": len(metadata_files),
            "pending_cleanup_count": len(pending_cleanup),
            "metadata_files": metadata_files,
            "pending_cleanup": pending_cleanup,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get temp storage stats: {str(e)}"
        ) from e


@router.post("/temp-storage/cleanup")
def cleanup_temp_storage(
    data: Optional[dict] = None, authenticated: bool = Depends(verify_api_key)
):
    """
    Clean up orphaned temporary storage (both memory and files)
    """
    data = data or {}
    try:
        cleanup_memory = data.get("cleanup_memory", True)
        cleanup_files = data.get("cleanup_files", True)
        max_age_hours = data.get("max_age_hours", 24)
        dry_run = data.get("dry_run", False)

        if max_age_hours < 1:
            raise HTTPException(
                status_code=400, detail="max_age_hours must be at least 1 hour."
            )

        if max_age_hours > 8760:
            raise HTTPException(
                status_code=400,
                detail="max_age_hours cannot exceed 8760 hours (1 year).",
            )

        results = {
            "dry_run": dry_run,
            "memory_cleanup": {},
            "file_cleanup": {},
            "metadata_cleanup": [],
        }

        if cleanup_memory:
            memory_storage = get_memory_storage()
            memory_items_before = memory_storage.get_size_info()["items_count"]

            if not dry_run:
                memory_storage.clear()
                memory_items_after = 0
            else:
                memory_items_after = memory_items_before

            results["memory_cleanup"] = {
                "items_before": memory_items_before,
                "items_after": memory_items_after,
                "items_cleaned": memory_items_before - memory_items_after,
            }

        if cleanup_files and os.path.exists(OUTPUT_DIR):
            files_cleaned = 0
            metadata_updated = 0

            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

            for filename in os.listdir(OUTPUT_DIR):
                if filename.endswith("_metadata.json"):
                    metadata_path = os.path.join(OUTPUT_DIR, filename)
                    try:
                        with open(metadata_path, "r", encoding="utf-8") as f:
                            metadata = json.load(f)

                        created_at = metadata.get("created_at")
                        if created_at:
                            created_time = datetime.fromisoformat(
                                created_at.replace("Z", "+00:00").replace("+00:00", "")
                            )

                            if created_time < cutoff_time and not metadata.get(
                                "cleanup_completed", False
                            ):
                                temp_file = metadata.get("temp_content_file")

                                if temp_file and os.path.exists(temp_file):
                                    if not dry_run:
                                        temp_manager = SecureTempFile(
                                            secure_delete=True
                                        )
                                        temp_manager.cleanup_file(temp_file)
                                        files_cleaned += 1

                                    results["metadata_cleanup"].append(
                                        {
                                            "metadata_file": filename,
                                            "temp_file": temp_file,
                                            "created_at": created_at,
                                            "action": (
                                                "cleaned"
                                                if not dry_run
                                                else "would_clean"
                                            ),
                                        }
                                    )

                                if not dry_run:
                                    metadata.pop("temp_content_file", None)
                                    metadata.pop("temp_storage_type", None)
                                    metadata.pop("job_id", None)
                                    metadata["cleanup_completed"] = True
                                    metadata["cleanup_at"] = datetime.now().isoformat()

                                    with open(metadata_path, "w", encoding="utf-8") as f:
                                        json.dump(metadata, f, indent=2)
                                    metadata_updated += 1

                    except Exception as e:
                        logger.warning(
                            f"Failed to process metadata file {filename}: {e}"
                        )

            results["file_cleanup"] = {
                "files_cleaned": files_cleaned,
                "metadata_updated": metadata_updated,
            }

        return {
            "success": True,
            "message": f"Temp storage cleanup {'completed' if not dry_run else 'simulated'}",
            "max_age_hours": max_age_hours,
            "environment": settings.environment,
            "results": results,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Temp storage cleanup failed: {str(e)}"
        ) from e

