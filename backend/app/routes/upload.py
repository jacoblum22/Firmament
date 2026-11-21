import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Header,
    HTTPException,
    Query,
    UploadFile,
)
from pydub import AudioSegment
from starlette.responses import StreamingResponse

from utils.security.auth import get_auth_manager
from utils.storage.content_cache import get_content_cache
from utils.common.error_messages import ErrorMessages
from utils.security.file_validator import FileValidationError, FileValidator
from utils.storage.s3_storage import get_storage_manager
from utils.storage.secure_temp_files import SecureTempFile, get_memory_storage

from ..config import settings
from .auth import get_current_user
from .constants import JOB_STATUS, OUTPUT_DIR, set_status

logger = logging.getLogger(__name__)

router = APIRouter(tags=["upload"])


def verify_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    api_key: Optional[str] = Query(None, description="API key for authentication"),
) -> bool:
    """
    Verify API key from header or query parameter.
    """
    provided_key = x_api_key or api_key
    expected_key = settings.api_key

    if settings.is_development:
        if not provided_key:
            logger.debug("Development mode: allowing unauthenticated request")
            return True
        if provided_key != expected_key:
            logger.warning("Development mode: invalid API key provided")
            raise HTTPException(
                status_code=401,
                detail="Invalid API key provided. Remove the key to proceed without authentication in development.",
            )
        return True

    if not expected_key:
        raise HTTPException(
            status_code=500,
            detail="API key not configured on server. Contact administrator.",
        )

    if not provided_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Provide via X-API-Key header or api_key query parameter.",
        )

    if provided_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key provided.")

    return True


def convert_m4a_to_wav(input_path: str) -> str:
    """
    Convert m4a file to wav format.

    Args:
        input_path: Path to the m4a file

    Returns:
        Path to the converted wav file
    """
    output_path = input_path.rsplit(".", 1)[0] + ".wav"
    audio = AudioSegment.from_file(input_path, format="m4a")
    audio.export(output_path, format="wav")
    return output_path


@router.get("/progress/{job_id}")
async def progress_stream(job_id: str):
    async def event_generator():
        while True:
            status = JOB_STATUS.get(job_id)
            if status is None:
                yield f"event: error\ndata: {json.dumps({'error': 'Invalid job ID'})}\n\n"
                break
            yield f"data: {json.dumps(status)}\n\n"

            if status.get("stage") in ["done", "error"]:
                break
            await asyncio.sleep(0.5)

    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "text/event-stream",
        "Connection": "keep-alive",
    }
    return StreamingResponse(event_generator(), headers=headers)


@router.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
):
    job_id = str(uuid4())
    set_status(job_id, stage="uploading")

    user_id = None
    if current_user:
        user_id = current_user["user_id"]
        logger.info(
            f"[{job_id[:8]}] Authenticated upload for user: {current_user['email']}"
        )
    elif settings.is_production:
        raise HTTPException(
            status_code=401,
            detail="Authentication required for file uploads in production",
        )
    else:
        logger.info(f"[{job_id[:8]}] Anonymous upload (development mode)")

    logger.info(
        f"[{job_id[:8]}] Upload: {file.filename}, Content-Type: {file.content_type}, Size: {file.size if hasattr(file, 'size') else 'unknown'}"
    )

    try:
        file_bytes = await file.read()
        logger.info(
            f"[{job_id[:8]}] File read successfully, size: {len(file_bytes)} bytes ({len(file_bytes)/(1024*1024):.1f}MB)"
        )
    except Exception as e:
        logger.error(f"[{job_id[:8]}] Failed to read file: {e}")
        raise HTTPException(
            status_code=400, detail=f"Failed to read uploaded file: {str(e)}"
        ) from e

    filename = file.filename or "uploaded_file"

    try:
        logger.info(f"[{job_id[:8]}] Starting file validation...")
        extension, safe_filename = FileValidator.validate_upload(file_bytes, filename)
        logger.info(
            f"[{job_id[:8]}] File validation passed: {extension}, {safe_filename}"
        )
    except FileValidationError as e:
        logger.warning(f"[{job_id[:8]}] File validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e

    def process_file(file_bytes: bytes, filename: str, safe_filename: str):
        try:
            ext = filename.split(".")[-1].lower()

            cache = get_content_cache()

            storage_manager = get_storage_manager()
            auth_manager = get_auth_manager()

            content_hash = auth_manager.get_user_content_hash(
                user_id or "anonymous", file_bytes
            )

            if user_id:
                user_storage_path = auth_manager.get_user_storage_path(
                    user_id, content_hash, "uploads"
                )
                cache_storage_path = auth_manager.get_user_storage_path(
                    user_id, content_hash, "cache"
                )
                shared_cache_path = auth_manager.get_shared_cache_path(content_hash)
            else:
                user_storage_path = f"uploads/anonymous/{content_hash}/"
                cache_storage_path = f"cache/anonymous/{content_hash}/"
                shared_cache_path = f"cache/shared/{content_hash}/"

            file_key = user_storage_path + safe_filename

            success = storage_manager.upload_file(
                file_bytes, file_key, file.content_type
            )
            if not success:
                raise Exception("Failed to save uploaded file")

            import tempfile

            with tempfile.NamedTemporaryFile(
                delete=False, suffix=f".{ext}"
            ) as temp_file:
                temp_file.write(file_bytes)
                file_location = temp_file.name

            set_status(job_id, stage="preprocessing")

            cached_processed = cache.get_processed_cache(file_bytes)
            if cached_processed:
                logger.info(
                    f"[{job_id[:8]}] Found cached processed data (content hash: {cached_processed['cache_info']['content_hash'][:8]}...)"
                )

                segments = cached_processed.get("segments", [])
                clusters = cached_processed.get("clusters", [])
                meta = cached_processed.get("meta", {})

                logger.info(
                    f"[{job_id[:8]}] Loaded from content cache - Segments: {len(segments)}, Clusters: {len(clusters)}"
                )

                full_text = "\n\n".join(
                    seg["text"] for seg in sorted(segments, key=lambda x: x["position"])
                )

                topics = {
                    str(cluster["cluster_id"]): {
                        "concepts": cluster.get("concepts", []),
                        "heading": cluster.get("heading", ""),
                        "summary": cluster.get("summary", ""),
                        "keywords": cluster.get("keywords", []),
                        "examples": cluster.get("examples", []),
                        "segment_positions": cluster.get("segment_positions", []),
                        "stats": cluster.get("stats", {}),
                        "bullet_points": cluster.get("bullet_points", []),
                        "references": cluster.get("references", []),
                        "code_snippet": cluster.get("code_snippet", ""),
                        "video_timestamp": cluster.get("video_timestamp", ""),
                        "note_summary": cluster.get("note_summary", ""),
                        "quiz_questions": cluster.get("quiz_questions", []),
                    }
                    for cluster in clusters
                }

                set_status(
                    job_id,
                    stage="done",
                    result={
                        "filename": file.filename,
                        "processing_id": content_hash,
                        "filetype": ext,
                        "text": full_text.strip(),
                        "message": "File processed successfully from cache.",
                        "segments": segments,
                        "topics": topics,
                        "cache_info": cached_processed["cache_info"],
                    },
                )

                try:
                    os.remove(file_location)
                except Exception as e:
                    logger.warning(
                        f"Failed to remove original file {file_location}: {e}"
                    )

                logger.info(
                    f"[{job_id[:8]}] Completed processing using cached processed data"
                )
                return

            cached_transcription = cache.get_transcription_cache(file_bytes)
            if cached_transcription:
                text = cached_transcription["text"]
                logger.info(
                    f"[{job_id[:8]}] Found cached transcription (content hash: {cached_transcription['cache_info']['content_hash'][:8]}...)"
                )
                logger.info(
                    f"[{job_id[:8]}] Using cached transcription, will process into topics..."
                )
            else:
                logger.info(f"[{job_id[:8]}] No cache found, processing file...")

            base_name = (file.filename or "uploaded_file").rsplit(".", 1)[0]
            output_filename = f"{content_hash}_transcription.txt"
            output_file_location = os.path.join(OUTPUT_DIR, output_filename)
            processed_path = os.path.join("processed", f"{content_hash}_processed.json")
            legacy_processed_path = os.path.join(
                "processed", f"{base_name}_processed.json"
            )

            _resolved_processed_path = (
                processed_path
                if os.path.exists(processed_path)
                else legacy_processed_path
            )
            if not cached_transcription and os.path.exists(_resolved_processed_path):
                processed_path = _resolved_processed_path
                with open(processed_path, "r", encoding="utf-8") as f:
                    processed_data = json.load(f)

                segments = processed_data.get("segments", [])
                clusters = processed_data.get("clusters", [])
                meta = processed_data.get("meta", {})

                logger.info(
                    f"[{job_id[:8]}] Loaded legacy cached JSON: {processed_path}"
                )
                logger.info(
                    f"[{job_id[:8]}] Segments: {len(segments)}, Clusters: {len(clusters)}"
                )
                logger.info(
                    f"Reconstructing transcript: {len(segments)} segments, "
                    f"words in segments: {meta.get('words_in_segments', 'N/A')}, "
                    f"in topics: {meta.get('words_in_topics', 'N/A')}, "
                    f"in noise: {meta.get('words_in_noise', 'N/A')}"
                )

                full_text = "\n\n".join(
                    seg["text"] for seg in sorted(segments, key=lambda x: x["position"])
                )

                reconstructed_words = len(full_text.split())
                logger.info(
                    f"Reconstruction: {reconstructed_words} words "
                    f"(expected {meta.get('words_in_segments', 'N/A')})"
                )
                topics = {
                    str(cluster["cluster_id"]): {
                        "concepts": cluster.get("concepts", []),
                        "heading": cluster.get("heading", ""),
                        "summary": cluster.get("summary", ""),
                        "keywords": cluster.get("keywords", []),
                        "examples": cluster.get("examples", []),
                        "segment_positions": cluster.get("segment_positions", []),
                        "stats": cluster.get("stats", {}),
                        "bullet_points": cluster.get("bullet_points", None),
                        "bullet_expansions": cluster.get("bullet_expansions", {}),
                    }
                    for cluster in clusters
                }

                try:
                    os.remove(file_location)
                except Exception as e:
                    logger.warning(
                        f"Failed to remove original file {file_location}: {e}"
                    )

                set_status(
                    job_id,
                    stage="done",
                    result={
                        "filename": file.filename,
                        "processing_id": content_hash,
                        "filetype": ext,
                        "text": full_text.strip(),
                        "message": "Using previously generated topics.",
                        "segments": segments,
                        "topics": topics,
                    },
                )
                return

            if os.path.exists(output_file_location):
                with open(output_file_location, "r", encoding="utf-8") as f:
                    existing_text = f.read().strip()

                try:
                    os.remove(file_location)
                except Exception as e:
                    logger.warning(
                        f"Failed to remove original file {file_location}: {e}"
                    )

                set_status(
                    job_id,
                    stage="done",
                    result={
                        "filename": file.filename,
                        "processing_id": content_hash,
                        "filetype": ext,
                        "text": existing_text,
                        "message": "Transcription file already exists. Skipping processing.",
                        "transcription_file": output_file_location,
                    },
                )
                return

            text = ""
            rnnoise_file = None

            if cached_transcription:
                text = cached_transcription["text"]
                logger.info(
                    f"[{job_id[:8]}] Using cached transcription text ({len(text)} characters)"
                )
            else:
                set_status(job_id, stage="transcribing")

                if ext == "pdf":
                    import fitz

                    with fitz.open(file_location) as doc:
                        for page in doc:
                            text += page.get_text()  # type: ignore

                elif ext == "txt":
                    with open(file_location, "r", encoding="utf-8") as f:
                        text = f.read()

                elif ext in ["mp3", "wav", "m4a"]:
                    try:
                        from utils.audio.transcribe_audio import transcribe_audio_in_chunks

                        if ext == "m4a":
                            logger.info("Converting m4a to wav...")
                            file_location = convert_m4a_to_wav(file_location)
                        text, rnnoise_file = transcribe_audio_in_chunks(
                            file_location,
                            progress_callback=lambda current, total: set_status(
                                job_id,
                                stage="transcribing",
                                current=current,
                                total=total,
                            ),
                        )

                    except FileNotFoundError as e:
                        if "ffmpeg" in str(e).lower():
                            error_info = ErrorMessages.get_user_friendly_error(
                                "ffmpeg_missing", str(e), {"file_type": ext}
                            )
                            set_status(job_id, stage="error", error=error_info["error"])
                            return error_info

                        error_info = ErrorMessages.get_user_friendly_error(
                            "file_not_found", str(e), {"file_type": ext}
                        )
                        set_status(job_id, stage="error", error=error_info["error"])
                        return error_info
                    except Exception as e:
                        error_info = ErrorMessages.get_user_friendly_error(
                            "audio_conversion_failed", str(e), {"file_type": ext}
                        )
                        set_status(job_id, stage="error", error=error_info["error"])
                        return error_info
                    finally:
                        if ext == "m4a" and file_location.endswith(".wav"):
                            try:
                                os.remove(file_location)
                            except Exception as e:
                                logger.warning(
                                    f"Failed to remove converted file {file_location}: {e}"
                                )

                if text.strip():
                    try:
                        content_hash = cache.save_transcription_cache(
                            file_bytes, text.strip(), filename, ext
                        )
                        logger.info(
                            f"[{job_id[:8]}] Saved transcription to content cache (hash: {content_hash[:8]}...)"
                        )
                    except Exception as cache_error:
                        logger.warning(
                            f"[{job_id[:8]}] Failed to save transcription cache: {cache_error}"
                        )

            set_status(job_id, stage="saving_output")
            with open(output_file_location, "w", encoding="utf-8") as f:
                f.write(text.strip())

            content_hash = cache.calculate_content_hash(file_bytes)

            memory_storage = get_memory_storage()
            temp_storage_type = "memory"
            temp_file_path = None
            temp_manager = None

            if memory_storage.store(
                f"{job_id}_{content_hash}",
                file_bytes,
                {
                    "original_filename": filename,
                    "file_extension": ext,
                    "created_at": datetime.now().isoformat(),
                    "job_id": job_id,
                },
            ):
                logger.info(
                    f"[{job_id[:8]}] Stored content securely in memory (hash: {content_hash[:8]}...)"
                )
            else:
                try:
                    temp_manager = SecureTempFile(
                        prefix=f"studymate_{base_name}_",
                        suffix=".bin",
                        secure_delete=True,
                        permissions=0o600,
                    )
                    temp_file_path = temp_manager.create_temp_file(
                        file_bytes, f"{job_id}_{content_hash}"
                    )
                    temp_storage_type = "secure_temp"
                    logger.info(
                        f"[{job_id[:8]}] Stored content in secure temp file with restricted permissions (hash: {content_hash[:8]}...)"
                    )
                except Exception as temp_error:
                    logger.warning(
                        f"[{job_id[:8]}] Failed to create secure temp file, falling back to memory cleanup: {temp_error}"
                    )
                    if temp_manager:
                        temp_manager.cleanup_all()
                    set_status(
                        job_id,
                        stage="error",
                        error="Failed to securely store temporary file",
                    )
                    return

            metadata_file = os.path.join(OUTPUT_DIR, f"{content_hash}_metadata.json")
            metadata = {
                "content_hash": content_hash,
                "original_filename": filename,
                "file_extension": ext,
                "created_at": datetime.now().isoformat(),
                "file_size": len(file_bytes),
                "temp_storage_type": temp_storage_type,
                "job_id": job_id,
                **(
                    {"temp_content_file": temp_file_path}
                    if temp_storage_type == "secure_temp"
                    else {}
                ),
            }
            try:
                with open(metadata_file, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, indent=2)
                logger.info(
                    f"[{job_id[:8]}] Saved metadata for potential topic generation (storage: {temp_storage_type})"
                )
            except Exception as e:
                logger.warning(f"[{job_id[:8]}] Failed to save metadata: {e}")
                if temp_storage_type == "memory":
                    memory_storage.remove(f"{job_id}_{content_hash}")
                elif temp_manager and temp_file_path:
                    temp_manager.cleanup_file(
                        temp_file_path, f"{job_id}_{content_hash}"
                    )

            try:
                os.remove(file_location)
                if rnnoise_file and os.path.exists(rnnoise_file):
                    os.remove(rnnoise_file)
                    logger.info(f"Deleted RNNoise file: {rnnoise_file}")
            except Exception as e:
                logger.warning(f"Failed to remove file {file_location}: {e}")

            set_status(
                job_id,
                stage="done",
                result={
                    "filename": file.filename,
                    "processing_id": content_hash,
                    "filetype": ext,
                    "text": text.strip(),
                    "message": f"{ext.upper()} file processed successfully.",
                    "transcription_file": output_file_location,
                },
            )
        except Exception as e:
            logger.error(f"[{job_id[:8]}] Processing error: {e}")

            try:
                if "content_hash" in locals():
                    memory_storage = get_memory_storage()
                    memory_storage.remove(f"{job_id}_{content_hash}")

                    if (
                        "temp_manager" in locals()
                        and temp_manager
                        and "temp_file_path" in locals()
                        and temp_file_path
                    ):
                        temp_manager.cleanup_file(
                            temp_file_path, f"{job_id}_{content_hash}"
                        )
                        logger.info(
                            f"[{job_id[:8]}] Cleaned up temporary storage on error"
                        )
            except Exception as cleanup_error:
                logger.warning(
                    f"[{job_id[:8]}] Failed to cleanup temporary storage on error: {cleanup_error}"
                )

            error_info = ErrorMessages.get_user_friendly_error(
                "processing_failed", str(e), {"filename": filename}
            )
            ErrorMessages.log_error_for_monitoring(
                "file_processing_error",
                str(e),
                {"job_id": job_id, "filename": filename},
            )
            set_status(job_id, stage="error", error=error_info["error"])
        finally:
            try:
                if "file_location" in locals() and os.path.exists(file_location):
                    os.remove(file_location)
                    logger.info(
                        f"[{job_id[:8]}] Cleaned up temporary file: {file_location}"
                    )
            except Exception as cleanup_error:
                logger.warning(
                    f"[{job_id[:8]}] Failed to cleanup temporary file: {cleanup_error}"
                )

    ext = filename.split(".")[-1].lower()
    if ext not in ["pdf", "mp3", "wav", "txt", "m4a"]:
        error_info = ErrorMessages.get_user_friendly_error(
            "invalid_request",
            f"Unsupported file type: .{ext}",
            {"supported_types": ["pdf", "mp3", "wav", "txt", "m4a"]},
        )
        return error_info

    background_tasks.add_task(process_file, file_bytes, filename, safe_filename)

    return {"job_id": job_id, "message": "Upload accepted. Processing started."}

