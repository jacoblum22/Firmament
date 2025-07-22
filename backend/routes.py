from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Header, Query
from starlette.responses import StreamingResponse
import os
from pydub import AudioSegment
import json
from uuid import uuid4
from fastapi import BackgroundTasks
import asyncio
from datetime import datetime, timedelta
from config import settings
from utils.file_validator import FileValidator, FileValidationError
from utils.error_messages import ErrorMessages
from utils.content_cache import get_content_cache
from typing import Dict, Any, Optional
from utils.secure_temp_files import SecureTempFile, get_memory_storage


# Fallback function for testing environments where utils may not be available
def fallback_debug_bullet_point(*args, **kwargs) -> Dict[str, Any]:
    return {"error": "bullet_point_debugger not available"}


# Authentication dependency for sensitive operations
def verify_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    api_key: Optional[str] = Query(None, description="API key for authentication"),
) -> bool:
    """
    Verify API key from header or query parameter.
    In development: authentication is optional (returns True if no key provided)
    In production: authentication is required
    """
    provided_key = x_api_key or api_key
    expected_key = settings.api_key

    # In development, allow requests without API key for easier testing
    if settings.is_development:
        if not provided_key:
            return True  # Allow unauthenticated access in dev
        # If key is provided in dev, it must be correct
        if provided_key != expected_key:
            raise HTTPException(
                status_code=401,
                detail="Invalid API key provided. Remove the key to proceed without authentication in development.",
            )
        return True

    # In production, always require authentication
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


def validate_max_age_days(max_age_days: int) -> int:
    """
    Validate max_age_days parameter for cache cleanup operations.

    Args:
        max_age_days: Number of days for maximum age

    Returns:
        int: Validated max_age_days value

    Raises:
        HTTPException: If validation fails
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


# Lazy import with fallback for testing environments
def get_bullet_point_debugger():
    try:
        from utils.bullet_point_debugger import debug_bullet_point

        return debug_bullet_point
    except ImportError:
        return fallback_debug_bullet_point
    except Exception as e:
        print(f"An error occurred: {e}")
        return fallback_debug_bullet_point


router = APIRouter()

# Get the absolute path to the backend directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(
    BASE_DIR, "output"
)  # Folder to save the extracted/transcribed text files
PROCESSED_DIR = os.path.join(BASE_DIR, "processed")

JOB_STATUS: dict[str, dict] = {}  # {job_id: {stage:…, current:…, total:…}}


def set_status(job_id: str, **kwargs):
    old_status = JOB_STATUS.get(job_id, {})
    new_status = {**old_status, **kwargs}
    JOB_STATUS[job_id] = new_status

    # Print to terminal
    stage = new_status.get("stage", "unknown")
    msg = f"[{job_id[:8]}] -> stage: {stage}"
    if "current" in new_status and "total" in new_status:
        msg += f" ({new_status['current']}/{new_status['total']})"
    if "error" in new_status:
        msg += f" [WARNING] error: {new_status['error']}"
    print(msg)


# Create the directories if they don't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


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
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    job_id = str(uuid4())
    set_status(job_id, stage="uploading")

    # Debug logging to help diagnose 422 errors
    print(f"[{job_id[:8]}] Upload request received:")
    print(f"[{job_id[:8]}] File: {file.filename}")
    print(f"[{job_id[:8]}] Content-Type: {file.content_type}")
    print(f"[{job_id[:8]}] Size: {file.size if hasattr(file, 'size') else 'unknown'}")

    # Read file content NOW, while request is active
    try:
        file_bytes = await file.read()
        print(
            f"[{job_id[:8]}] File read successfully, size: {len(file_bytes)} bytes ({len(file_bytes)/(1024*1024):.1f}MB)"
        )
    except Exception as e:
        print(f"[{job_id[:8]}] Failed to read file: {e}")
        raise HTTPException(
            status_code=400, detail=f"Failed to read uploaded file: {str(e)}"
        ) from e

    filename = file.filename or "uploaded_file"

    try:
        # Comprehensive file validation
        print(f"[{job_id[:8]}] Starting file validation...")
        extension, safe_filename = FileValidator.validate_upload(file_bytes, filename)
        print(f"[{job_id[:8]}] File validation passed: {extension}, {safe_filename}")
    except FileValidationError as e:
        print(f"[{job_id[:8]}] File validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e

    def process_file(file_bytes: bytes, filename: str, safe_filename: str):
        try:
            ext = filename.split(".")[-1].lower()

            # Initialize content cache
            cache = get_content_cache()

            # Use safe filename for file operations
            file_location = os.path.join(UPLOAD_DIR, safe_filename)

            # Save the original file to the 'uploads' folder
            with open(file_location, "wb") as f:
                f.write(file_bytes)

            set_status(job_id, stage="preprocessing")

            # Check for cached processed data first (most complete cache)
            cached_processed = cache.get_processed_cache(file_bytes)
            if cached_processed:
                print(
                    f"[{job_id[:8]}] Found cached processed data (content hash: {cached_processed['cache_info']['content_hash'][:8]}...)"
                )

                segments = cached_processed.get("segments", [])
                clusters = cached_processed.get("clusters", [])
                meta = cached_processed.get("meta", {})

                print(
                    f"[{job_id[:8]}] Loaded from content cache - Segments: {len(segments)}, Clusters: {len(clusters)}"
                )

                # Sort segments by position to reconstruct full transcript
                full_text = "\n\n".join(
                    seg["text"] for seg in sorted(segments, key=lambda x: x["position"])
                )

                # Convert cluster structure to match TopicResponse in frontend
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

                # Use the same structure as legacy cached data for frontend compatibility
                set_status(
                    job_id,
                    stage="done",
                    result={
                        "filename": file.filename,
                        "filetype": ext,
                        "text": full_text.strip(),
                        "message": "File processed successfully from cache.",
                        "segments": segments,  # Include segments for frontend chunk access
                        "topics": topics,
                        "cache_info": cached_processed["cache_info"],
                    },
                )

                # Clean up the original file since we're using cached data
                try:
                    os.remove(file_location)
                except Exception as e:
                    print(
                        f"Warning: Failed to remove original file {file_location}: {e}"
                    )

                print(
                    f"[{job_id[:8]}] Completed processing using cached processed data"
                )
                return

            # Check for cached transcription (partial cache)
            cached_transcription = cache.get_transcription_cache(file_bytes)
            if cached_transcription:
                text = cached_transcription["text"]
                print(
                    f"[{job_id[:8]}] Found cached transcription (content hash: {cached_transcription['cache_info']['content_hash'][:8]}...)"
                )
                print(
                    f"[{job_id[:8]}] Using cached transcription, will process into topics..."
                )
            else:
                # No cache found, need to transcribe/extract text
                print(f"[{job_id[:8]}] No cache found, processing file...")

            # Define paths for legacy compatibility
            base_name = (file.filename or "uploaded_file").rsplit(".", 1)[0]
            output_filename = f"{base_name}_transcription.txt"
            output_file_location = os.path.join(OUTPUT_DIR, output_filename)
            processed_path = os.path.join("processed", f"{base_name}_processed.json")

            # Check for legacy filename-based cache if no content cache exists
            if not cached_transcription and os.path.exists(processed_path):
                with open(processed_path, "r", encoding="utf-8") as f:
                    processed_data = json.load(f)

                segments = processed_data.get("segments", [])
                clusters = processed_data.get("clusters", [])
                meta = processed_data.get("meta", {})

                print(f"[{job_id[:8]}] Loaded legacy cached JSON: {processed_path}")
                print(
                    f"[{job_id[:8]}] Segments: {len(segments)}, Clusters: {len(clusters)}"
                )
                print(f"\nReconstructing transcript from JSON:")
                print(f"Number of segments in JSON: {len(segments)}")
                print(
                    f"Total words in segments: {meta.get('words_in_segments', 'N/A')}"
                )
                print(f"Words in topics: {meta.get('words_in_topics', 'N/A')}")
                print(f"Words in noise: {meta.get('words_in_noise', 'N/A')}")

                # Sort segments by position to reconstruct full transcript
                full_text = "\n\n".join(
                    seg["text"] for seg in sorted(segments, key=lambda x: x["position"])
                )

                # Print reconstruction stats
                reconstructed_words = len(full_text.split())
                print(f"\nReconstruction stats:")
                print(f"Words in reconstructed text: {reconstructed_words}")
                print(
                    f"Expected words from segments: {meta.get('words_in_segments', 'N/A')}"
                )
                if meta.get("words_in_segments"):
                    print(
                        f"Word count difference: {reconstructed_words - meta.get('words_in_segments')}"
                    )  # Convert cluster structure to match TopicResponse in frontend
                topics = {
                    str(cluster["cluster_id"]): {
                        "concepts": cluster.get("concepts", []),
                        "heading": cluster.get("heading", ""),
                        "summary": cluster.get("summary", ""),  # Include summary field
                        "keywords": cluster.get("keywords", []),
                        "examples": cluster.get("examples", []),
                        "segment_positions": cluster.get(
                            "segment_positions", []
                        ),  # Include segment_positions for full chunk access
                        "stats": cluster.get("stats", {}),
                        "bullet_points": cluster.get(
                            "bullet_points", None
                        ),  # Include bullet_points if they exist
                        "bullet_expansions": cluster.get(
                            "bullet_expansions", {}
                        ),  # Include bullet_expansions if they exist
                    }
                    for cluster in clusters
                }

                # Clean up the original file since we're using cached data
                try:
                    os.remove(file_location)
                except Exception as e:
                    print(
                        f"Warning: Failed to remove original file {file_location}: {e}"
                    )

                set_status(
                    job_id,
                    stage="done",
                    result={
                        "filename": file.filename,
                        "filetype": ext,
                        "text": full_text.strip(),
                        "message": "Using previously generated topics.",
                        "segments": segments,  # Include segments for frontend chunk access
                        "topics": topics,
                    },
                )
                return

            # If just the transcription exists (but not processed data)
            if os.path.exists(output_file_location):
                with open(output_file_location, "r", encoding="utf-8") as f:
                    existing_text = f.read().strip()

                # Clean up the original file since we're using cached transcription
                try:
                    os.remove(file_location)
                except Exception as e:
                    print(
                        f"Warning: Failed to remove original file {file_location}: {e}"
                    )

                set_status(
                    job_id,
                    stage="done",
                    result={
                        "filename": file.filename,
                        "filetype": ext,
                        "text": existing_text,
                        "message": "Transcription file already exists. Skipping processing.",
                        "transcription_file": output_file_location,
                    },
                )
                return

            # Process transcription (use cache if available)
            text = ""
            rnnoise_file = None

            if cached_transcription:
                # Use cached transcription
                text = cached_transcription["text"]
                print(
                    f"[{job_id[:8]}] Using cached transcription text ({len(text)} characters)"
                )
            else:
                # No transcription cache, need to process the file
                set_status(job_id, stage="transcribing")

                # Extract text for PDF files
                if ext == "pdf":
                    import fitz  # PyMuPDF

                    with fitz.open(file_location) as doc:
                        for page in doc:
                            text += page.get_text()  # type: ignore

                # Extract text for TXT files
                elif ext == "txt":
                    with open(file_location, "r", encoding="utf-8") as f:
                        text = f.read()

                # Extract text for audio files
                elif ext in ["mp3", "wav", "m4a"]:
                    try:
                        from utils.transcribe_audio import transcribe_audio_in_chunks

                        # Convert m4a to wav if necessary
                        if ext == "m4a":
                            print("Converting m4a to wav...")
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
                        # Clean up converted wav file if it was created
                        if ext == "m4a" and file_location.endswith(".wav"):
                            try:
                                os.remove(file_location)
                            except Exception as e:
                                print(
                                    f"Warning: Failed to remove converted file {file_location}: {e}"
                                )

                # Save new transcription to content cache
                if text.strip():
                    try:
                        content_hash = cache.save_transcription_cache(
                            file_bytes, text.strip(), filename, ext
                        )
                        print(
                            f"[{job_id[:8]}] Saved transcription to content cache (hash: {content_hash[:8]}...)"
                        )
                    except Exception as cache_error:
                        print(
                            f"[{job_id[:8]}] Warning: Failed to save transcription cache: {cache_error}"
                        )

            # Save the transcribed/extracted text to a file in the 'output' folder (for legacy compatibility)
            set_status(job_id, stage="saving_output")
            with open(output_file_location, "w", encoding="utf-8") as f:
                f.write(text.strip())

            # Save original file content and metadata for potential topic generation
            content_hash = cache.calculate_content_hash(file_bytes)

            # Try to store in memory first for better security (avoid disk I/O)
            memory_storage = get_memory_storage()
            temp_storage_type = "memory"
            temp_file_path = None
            temp_manager = None

            # Check if file is small enough for in-memory storage
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
                print(
                    f"[{job_id[:8]}] Stored content securely in memory (hash: {content_hash[:8]}...)"
                )
            else:
                # Fallback to secure temporary file for large files
                try:
                    temp_manager = SecureTempFile(
                        prefix=f"studymate_{base_name}_",
                        suffix=".bin",
                        secure_delete=True,
                        permissions=0o600,  # Owner read/write only
                    )
                    temp_file_path = temp_manager.create_temp_file(
                        file_bytes, f"{job_id}_{content_hash}"
                    )
                    temp_storage_type = "secure_temp"
                    print(
                        f"[{job_id[:8]}] Stored content in secure temp file with restricted permissions (hash: {content_hash[:8]}...)"
                    )
                except Exception as temp_error:
                    print(
                        f"[{job_id[:8]}] Warning: Failed to create secure temp file, falling back to memory cleanup: {temp_error}"
                    )
                    # Force cleanup and fail gracefully
                    if temp_manager:
                        temp_manager.cleanup_all()
                    set_status(
                        job_id,
                        stage="error",
                        error="Failed to securely store temporary file",
                    )
                    return

            # Save metadata (avoid storing raw file path in metadata for security)
            metadata_file = os.path.join(OUTPUT_DIR, f"{base_name}_metadata.json")
            metadata = {
                "content_hash": content_hash,
                "original_filename": filename,
                "file_extension": ext,
                "created_at": datetime.now().isoformat(),
                "file_size": len(file_bytes),
                "temp_storage_type": temp_storage_type,
                "job_id": job_id,
                # Only store temp file path if using secure temp file (not memory)
                **(
                    {"temp_content_file": temp_file_path}
                    if temp_storage_type == "secure_temp"
                    else {}
                ),
            }
            try:
                with open(metadata_file, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, indent=2)
                print(
                    f"[{job_id[:8]}] Saved metadata for potential topic generation (storage: {temp_storage_type})"
                )
            except Exception as e:
                print(f"[{job_id[:8]}] Warning: Failed to save metadata: {e}")
                # Clean up temp storage if metadata save failed
                if temp_storage_type == "memory":
                    memory_storage.remove(f"{job_id}_{content_hash}")
                elif temp_manager and temp_file_path:
                    temp_manager.cleanup_file(
                        temp_file_path, f"{job_id}_{content_hash}"
                    )

            # Clean up files
            try:
                # Remove original file
                os.remove(file_location)
                # Remove RNNoise file if it was created
                if rnnoise_file and os.path.exists(rnnoise_file):
                    os.remove(rnnoise_file)
                    print(f"Deleted RNNoise file: {rnnoise_file}")
            except Exception as e:
                print(f"Warning: Failed to remove file {file_location}: {e}")

            set_status(
                job_id,
                stage="done",
                result={
                    "filename": file.filename,
                    "filetype": ext,
                    "text": text.strip(),
                    "message": f"{ext.upper()} file processed successfully.",
                    "transcription_file": output_file_location,
                },
            )
        except Exception as e:
            print(f"[{job_id[:8]}] [ERROR]: {e}")

            # Clean up any temporary storage on error
            try:
                # Try to clean up based on job_id and content hash if available
                if "content_hash" in locals():
                    memory_storage = get_memory_storage()
                    memory_storage.remove(f"{job_id}_{content_hash}")

                    # Clean up secure temp file if it was created
                    if (
                        "temp_manager" in locals()
                        and temp_manager
                        and "temp_file_path" in locals()
                        and temp_file_path
                    ):
                        temp_manager.cleanup_file(
                            temp_file_path, f"{job_id}_{content_hash}"
                        )
                        print(f"[{job_id[:8]}] Cleaned up temporary storage on error")
            except Exception as cleanup_error:
                print(
                    f"[{job_id[:8]}] Warning: Failed to cleanup temporary storage on error: {cleanup_error}"
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

    # Validate file extension before processing
    ext = filename.split(".")[-1].lower()
    if ext not in ["pdf", "mp3", "wav", "txt", "m4a"]:
        error_info = ErrorMessages.get_user_friendly_error(
            "invalid_request",
            f"Unsupported file type: .{ext}",
            {"supported_types": ["pdf", "mp3", "wav", "txt", "m4a"]},
        )
        return error_info

    # Start background task and pass the raw data
    background_tasks.add_task(process_file, file_bytes, filename, safe_filename)

    return {"job_id": job_id, "message": "Upload accepted. Processing started."}


# Lazy import utils modules
def get_semantic_segment():
    try:
        from utils.semantic_segmentation import semantic_segment

        return semantic_segment
    except ImportError:

        def semantic_segment(text, similarity_threshold=0.3):
            return [
                {"start": 0, "end": len(text), "text": text}
            ]  # Fallback: return whole text as single segment

        return semantic_segment


def get_filter_chunks():
    try:
        from utils.filter_chunks import filter_chunks

        return filter_chunks
    except ImportError:

        def filter_chunks(chunks, min_words=5, max_stopword_ratio=0.9):
            return chunks  # Fallback: return chunks unchanged

        return filter_chunks


def get_optimize_chunk_sizes():
    try:
        from utils.chunk_size_optimizer import optimize_chunk_sizes

        return optimize_chunk_sizes
    except ImportError:

        def optimize_chunk_sizes(chunks, min_words=50, max_words=150, target_size=100):
            return chunks  # Fallback: return chunks unchanged

        return optimize_chunk_sizes


def get_bertopic_processor():
    try:
        from utils.bertopic_processor import process_with_bertopic

        return process_with_bertopic
    except ImportError:

        def process_with_bertopic(chunks, filename=None):
            return {
                "topics": {},
                "num_chunks": len(chunks),
                "num_topics": 0,
                "total_tokens_used": 0,
            }

        return process_with_bertopic


@router.post("/test-bertopic")
def test_bertopic(data: dict):
    text = data.get("text", "")
    full_filename = data.get("filename") or "default"  # Get filename from request
    filename = os.path.splitext(full_filename)[
        0
    ]  # Step 1: Segment → Filter → Optimize (using our improved pipeline)

    # Use lazy-loaded functions
    semantic_segment = get_semantic_segment()
    filter_chunks = get_filter_chunks()
    optimize_chunk_sizes = get_optimize_chunk_sizes()
    process_with_bertopic = get_bertopic_processor()

    raw_chunks = semantic_segment(text, similarity_threshold=0.5)
    filtered_chunks = filter_chunks(raw_chunks, min_words=4, max_stopword_ratio=0.75)
    chunks = optimize_chunk_sizes(
        filtered_chunks, min_words=75, max_words=150, target_size=125
    )

    # Step 2: Process with BERTopic
    result = process_with_bertopic(chunks, filename)

    # Convert result to match frontend expectations
    return {
        "num_chunks": result["num_chunks"],
        "num_topics": result["num_topics"],
        "total_tokens_used": result["total_tokens_used"],
        "topics": result["topics"],
    }


@router.post("/process-chunks")
def process_chunks(data: dict):
    text = data.get("text", "")
    full_filename = data.get("filename", "default")
    filename = os.path.splitext(full_filename)[0]  # Step 1: Chunking pipeline

    # Use lazy-loaded functions
    semantic_segment = get_semantic_segment()
    filter_chunks = get_filter_chunks()
    optimize_chunk_sizes = get_optimize_chunk_sizes()

    raw_chunks = semantic_segment(text, similarity_threshold=0.5)
    filtered_chunks = filter_chunks(raw_chunks, min_words=4, max_stopword_ratio=0.75)
    chunks = optimize_chunk_sizes(
        filtered_chunks, min_words=50, max_words=100, target_size=75
    )

    # Step 2: Save the chunks to disk
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    processed_path = os.path.join(PROCESSED_DIR, f"{filename}_chunks.json")
    with open(processed_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "chunks": chunks,
                "meta": {
                    "total_words": sum(len(c["text"].split()) for c in chunks),
                    "num_chunks": len(chunks),
                },
            },
            f,
            indent=2,
        )

    word_counts = [len(c["text"].split()) for c in chunks]
    min_words = min(word_counts) if word_counts else 0
    max_words = max(word_counts) if word_counts else 0
    avg_words = round(sum(word_counts) / len(word_counts), 2) if word_counts else 0

    # Calculate second-minimum to show actual minimum compliance (excluding the one allowed outlier)
    second_min_words = min_words
    if len(word_counts) >= 2:
        sorted_counts = sorted(word_counts)
        second_min_words = sorted_counts[1]  # Second smallest value

    print(f"\n[CHUNKING] Chunking Summary for '{filename}':")
    print(f"Total Chunks: {len(chunks)}")
    print(
        f"Words per Chunk -> second-min: {second_min_words}, max: {max_words}, avg: {avg_words}"
    )

    return {
        "message": "Chunks saved successfully.",
        "filename": filename,
        "num_chunks": len(chunks),
        "total_words": sum(word_counts),
        "chunk_stats": {
            "second_min": second_min_words,
            "max": max_words,
            "avg": avg_words,
        },
    }


@router.post("/generate-headings")
def generate_headings(data: dict):
    full_filename = data.get("filename")
    if not full_filename:
        return {"error": "Filename is required."}
    filename = os.path.splitext(full_filename)[0]

    chunk_file = os.path.join("processed", f"{filename}_chunks.json")
    processed_file = os.path.join("processed", f"{filename}_processed.json")
    chunks = []
    # Try to load chunks from _chunks.json, else fallback to _processed.json
    if os.path.exists(chunk_file):
        with open(chunk_file, "r", encoding="utf-8") as f:
            chunk_data = json.load(f)
            chunks = chunk_data.get("chunks", [])
    elif os.path.exists(processed_file):
        with open(processed_file, "r", encoding="utf-8") as f:
            processed_data = json.load(f)
            chunks = processed_data.get("segments", [])
    else:
        error_info = ErrorMessages.get_user_friendly_error(
            "file_not_found",
            f"Chunks not found for filename: {filename}",
            {"filename": filename},
        )
        return error_info

    # Run BERTopic
    process_with_bertopic = get_bertopic_processor()
    result = process_with_bertopic(chunks, filename)

    # Save full result to legacy format
    processed_path = os.path.join("processed", f"{filename}_processed.json")
    with open(processed_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    # Save processed data to content cache if we have the original file content
    metadata_file = os.path.join(OUTPUT_DIR, f"{filename}_metadata.json")
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            temp_content_file = metadata.get("temp_content_file")
            content_hash = metadata.get("content_hash")
            original_filename = metadata.get("original_filename", full_filename)
            temp_storage_type = metadata.get(
                "temp_storage_type", "legacy"
            )  # Default to legacy for backwards compatibility
            job_id = metadata.get("job_id")

            file_bytes = None

            # Handle different storage types securely
            if temp_storage_type == "memory" and content_hash and job_id:
                # Try to retrieve from memory storage
                memory_storage = get_memory_storage()
                file_bytes = memory_storage.retrieve(f"{job_id}_{content_hash}")
                if file_bytes:
                    print(
                        f"Retrieved file content from secure memory storage (hash: {content_hash[:8]}...)"
                    )
                else:
                    print(
                        f"Warning: File content not found in memory storage, may have been cleaned up"
                    )

            elif (
                temp_storage_type == "secure_temp"
                and temp_content_file
                and os.path.exists(temp_content_file)
            ):
                # Read from secure temp file
                try:
                    with open(temp_content_file, "rb") as f:
                        file_bytes = f.read()
                    logger.info(
                        f"Retrieved file content from secure temp file (hash: {content_hash[:8] if content_hash else 'unknown'}...)"
                    )
                except Exception as read_error:
                    logger.warning(
                        f"Failed to read secure temp file {temp_content_file}: {read_error}"
                    )

            elif (
                temp_content_file and os.path.exists(temp_content_file) and content_hash
            ):
                # Legacy support for old temp files
                try:
                    with open(temp_content_file, "rb") as f:
                        file_bytes = f.read()
                    print(
                        f"Retrieved file content from legacy temp file (hash: {content_hash[:8]}...)"
                    )
                except Exception as read_error:
                    print(
                        f"Warning: Failed to read legacy temp file {temp_content_file}: {read_error}"
                    )

            if file_bytes and content_hash:
                # Save processed data to content cache
                cache = get_content_cache()
                try:
                    saved_hash = cache.save_processed_cache(
                        file_bytes, result, original_filename
                    )
                    print(
                        f"Saved processed data to content cache (hash: {saved_hash[:8]}...)"
                    )
                except Exception as cache_error:
                    print(
                        f"Warning: Failed to save processed data to cache: {cache_error}"
                    )

                # Clean up temporary storage after successful caching
                try:
                    if temp_storage_type == "memory" and job_id:
                        memory_storage = get_memory_storage()
                        if memory_storage.remove(f"{job_id}_{content_hash}"):
                            print(f"Cleaned up memory storage for job {job_id}")
                    elif temp_content_file and os.path.exists(temp_content_file):
                        # For both secure_temp and legacy files, use secure deletion
                        temp_manager = SecureTempFile(secure_delete=True)
                        if temp_manager.cleanup_file(temp_content_file):
                            print(
                                f"Securely cleaned up temporary content file: {temp_content_file}"
                            )
                        else:
                            # Fallback to regular deletion if secure deletion fails
                            os.remove(temp_content_file)
                            print(
                                f"Cleaned up temporary content file (fallback): {temp_content_file}"
                            )
                except Exception as cleanup_error:
                    print(f"Warning: Failed to clean up temp storage: {cleanup_error}")

                # Update metadata to remove temp file reference and add caching info
                metadata.pop("temp_content_file", None)
                metadata.pop("temp_storage_type", None)
                metadata.pop("job_id", None)  # Remove job_id after cleanup
                metadata["cached_at"] = datetime.now().isoformat()
                metadata["cleanup_completed"] = True
                with open(metadata_file, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, indent=2)

        except Exception as e:
            print(
                f"Warning: Failed to process content cache during topic generation: {e}"
            )

    return {
        "message": "Topics generated successfully.",
        "num_topics": result["num_topics"],
        "num_chunks": result.get("num_chunks", 0),
        "total_tokens_used": result.get("total_tokens_used", 0),
        "segments": result.get("segments", chunks),  # Include segments for frontend
        "topics": result["topics"],
    }


@router.post("/expand-cluster")
def expand_cluster(data: dict):
    """
    Expand a specific cluster in the processed file for the given filename and cluster ID.

    Args:
        data (dict): A dictionary containing 'filename' (str) and 'cluster_id' (str or int).

    Returns:
        dict:
            On success, returns a dictionary with expanded cluster information, e.g.:
    full_filename = data.get("filename")
    cluster_id = data.get("cluster_id")

    if full_filename is None or cluster_id is None:
        return ErrorMessages.get_user_friendly_error(
            "invalid_request",
            "Missing filename or cluster_id",
            {"operation": "cluster expansion", "required_fields": ["filename", "cluster_id"]}
        )

    # Validate and convert cluster_id to int if possible
    try:
        cluster_id = int(cluster_id)
    except (ValueError, TypeError):
        return ErrorMessages.get_user_friendly_error(
            "invalid_request",
            f"Invalid cluster_id format: {cluster_id}",
            {"operation": "cluster expansion", "expected_type": "integer", "received_value": str(cluster_id)}
        )

    # Prepare the filename relative to the 'processed' folder as expected by expand_cluster
    processed_filename = os.path.splitext(full_filename)[0] + "_processed.json"

    from utils.expand_cluster import expand_cluster as expand_cluster_util

    # Pass only the filename (not the full path) to expand_cluster
    result = expand_cluster_util(processed_filename, cluster_id)
    return result
        - Processed file not found or invalid.
        - Cluster ID not found in the processed data.
    """
    full_filename = data.get("filename")
    cluster_id = data.get("cluster_id")

    if full_filename is None or cluster_id is None:
        return {"error": "Filename and cluster ID are required."}

    # Prepare the filename relative to the 'processed' folder as expected by expand_cluster
    processed_filename = os.path.splitext(full_filename)[0] + "_processed.json"

    from utils.expand_cluster import expand_cluster as expand_cluster_util

    # Pass only the filename (not the full path) to expand_cluster
    result = expand_cluster_util(processed_filename, cluster_id)
    return result


@router.post("/debug-bullet-point")
def debug_bullet_point_endpoint(data: dict):
    """
    Debug a bullet point by finding its most similar chunk and comparing it to other topics.

    Args:
        data (dict): A dictionary containing 'bullet_point' (str), 'chunks' (list of str), and 'topics' (dict).

    Returns:
        dict: Debugging result including the most similar chunk, similarity to the current topic, and topic similarities.
    """
    from typing import Dict, Any

    bullet_point = data.get("bullet_point")
    chunks = data.get("chunks", [])
    topics = data.get("topics", {})

    if not bullet_point or not chunks or not topics:
        return ErrorMessages.get_user_friendly_error(
            "invalid_request",
            "Missing bullet_point, chunks, or topics",
            {
                "operation": "bullet point analysis",
                "required_fields": ["bullet_point", "chunks", "topics"],
            },
        )

    try:
        debug_bullet_point = get_bullet_point_debugger()
        result: Dict[str, Any] = debug_bullet_point(bullet_point, chunks, topics)

        # Convert numpy types to native Python types
        result["similarity_to_current_topic"] = float(
            result["similarity_to_current_topic"]
        )

        # Convert top_similar_chunks similarities to float
        if "top_similar_chunks" in result:
            result["top_similar_chunks"] = [
                {"chunk": chunk["chunk"], "similarity": float(chunk["similarity"])}
                for chunk in result["top_similar_chunks"]
            ]

        topic_similarities = result.get("topic_similarities")
        if isinstance(topic_similarities, dict):
            result["topic_similarities"] = {
                key: float(value) for key, value in topic_similarities.items()
            }
        else:
            result["topic_similarities"] = {}

        return result
    except Exception as e:
        error_info = ErrorMessages.get_user_friendly_error(
            "processing_failed", str(e), {"operation": "bullet point analysis"}
        )
        return error_info


@router.post("/expand-bullet-point")
def expand_bullet_point_endpoint(data: dict):
    """
    Expand a bullet point with additional detail and context.

    Args:
        data (dict): A dictionary containing:
            - 'bullet_point' (str): The bullet point to expand
            - 'chunks' (list of str): Text chunks from the topic
            - 'topic_heading' (str): The topic heading
            - 'filename' (str): The filename for saving
            - 'topic_id' (str): The topic ID
            - 'layer' (int, optional): Expansion layer (default: 1)
            - 'other_bullets' (list, optional): Other bullets in the topic to avoid duplication

    Returns:
        dict: Expansion result including the original bullet point and expanded content.
    """
    bullet_point = data.get("bullet_point")
    chunks = data.get("chunks", [])
    topic_heading = data.get("topic_heading", "Unknown Topic")
    filename = data.get("filename")
    topic_id = data.get("topic_id")
    layer = data.get("layer", 1)  # Default to layer 1 if not specified
    other_bullets = data.get("other_bullets", [])  # Get other bullets in the topic

    print(f"\n[EXPAND] Bullet point endpoint called")
    print(f"[BULLET] Bullet point: {bullet_point[:50] if bullet_point else 'None'}...")
    print(f"[CHUNKS] Received {len(chunks)} chunks for expansion")
    print(f"[OTHER_BULLETS] Received {len(other_bullets)} other bullets for context")
    print(f"[TOPIC] Topic heading: {topic_heading}")
    print(f"[FILE] Filename: {filename}")
    print(f"[ID] Topic ID: {topic_id}")
    print(f"[LAYER] Expansion layer: {layer}")

    if not bullet_point or not chunks:
        error_msg = "Missing required fields: 'bullet_point' or 'chunks'."
        print(f"[ERROR] Error: {error_msg}")
        return {"error": error_msg}

    try:
        from utils.expand_bullet_point import expand_bullet_point

        result = expand_bullet_point(
            bullet_point, chunks, topic_heading, layer, other_bullets
        )
        print(f"[SUCCESS] Expansion completed successfully")

        # Save the expansion to the processed JSON file
        if filename and topic_id and not result.get("error"):
            try:
                from utils.save_bullet_expansion import save_bullet_expansion

                base_name = os.path.splitext(filename)[0]
                processed_file = os.path.join(
                    "processed", f"{base_name}_processed.json"
                )

                if os.path.exists(processed_file):
                    with open(processed_file, "r", encoding="utf-8") as f:
                        processed_data = json.load(f)

                    # Prepare expansion data
                    expansion_data = {
                        "expanded_bullets": result.get("expanded_bullets", []),
                        "topic_heading": topic_heading,
                        "chunks_used": result.get("chunks_used", 0),
                    }

                    # Get parent bullet for layer 2 expansions
                    parent_bullet = data.get("parent_bullet") if layer == 2 else None

                    # Save the expansion using the utility function
                    success = save_bullet_expansion(
                        processed_data=processed_data,
                        topic_id=topic_id,
                        bullet_point=bullet_point,
                        expansion_data=expansion_data,
                        layer=layer,
                        parent_bullet=parent_bullet,
                    )

                    if success:
                        # Save back to file
                        with open(processed_file, "w", encoding="utf-8") as f:
                            json.dump(processed_data, f, indent=2)
                        print(
                            f"[SAVE] Saved expansion to cluster {topic_id} in {processed_file}"
                        )
                    else:
                        print(
                            f"[WARNING] Failed to save expansion using utility function"
                        )
                else:
                    print(f"[WARNING] Processed file not found: {processed_file}")
            except Exception as save_error:
                print(f"[WARNING] Failed to save expansion: {save_error}")
                # Don't fail the request if saving fails

        return result
    except Exception as e:
        error_msg = f"Failed to expand bullet point: {str(e)}"
        print(f"[ERROR]: {error_msg}")
        return {"error": error_msg}


# Optional cleanup management endpoints (disabled by default for security)
@router.get("/cleanup/status")
def get_cleanup_status():
    """Get cleanup service status (requires debug mode)"""
    if not settings.debug:
        raise HTTPException(status_code=404, detail="Endpoint not available")

    try:
        from utils.cleanup_service import get_cleanup_service

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

    Requires API key authentication in production.
    In development, authentication is optional but recommended.

    Args:
        dry_run: Whether to perform a dry run (default: True for safety)
        authenticated: Authentication dependency (automatically injected)
    """
    if not settings.debug:
        raise HTTPException(status_code=404, detail="Endpoint not available")

    try:
        from utils.cleanup_service import get_cleanup_service

        service = get_cleanup_service()
        results = service.run_manual_cleanup(dry_run=dry_run)
        return {
            "message": "Cleanup completed" if not dry_run else "Dry run completed",
            "dry_run": dry_run,
            "environment": settings.environment,
            "results": results,
        }
    except HTTPException:
        # Re-raise HTTP exceptions (authentication errors)
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
def cleanup_cache(data: dict = {}, authenticated: bool = Depends(verify_api_key)):
    """
    Clean up old cache entries

    Requires API key authentication in production.
    In development, authentication is optional but recommended.

    Args:
        data: Dictionary containing optional max_age_days parameter
        authenticated: Authentication dependency (automatically injected)

    Returns:
        dict: Cleanup results and statistics

    Raises:
        HTTPException: For authentication or validation failures
    """
    try:
        cache = get_content_cache()

        # Get and validate max_age_days
        max_age_days = 30  # Conservative default

        if data and "max_age_days" in data:
            try:
                max_age_days = int(data["max_age_days"])
                max_age_days = validate_max_age_days(max_age_days)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="max_age_days must be a valid integer."
                )

        cleanup_stats = cache.cleanup_old_entries(max_age_days)

        return {
            "success": True,
            "message": f"Cache cleanup completed for entries older than {max_age_days} days",
            "max_age_days": max_age_days,
            "stats": cleanup_stats,
            "environment": settings.environment,
        }
    except HTTPException:
        # Re-raise HTTP exceptions (authentication, validation errors)
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

        # Count metadata files that might reference temp storage
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

                        # Check if cleanup is needed
                        if (
                            not metadata.get("cleanup_completed", False)
                            and "temp_content_file" in metadata
                        ):
                            pending_cleanup.append(filename)

                    except Exception as e:
                        print(f"Warning: Failed to read metadata file {filename}: {e}")

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
    data: dict = {}, authenticated: bool = Depends(verify_api_key)
):
    """
    Clean up orphaned temporary storage (both memory and files)

    Requires API key authentication in production.
    In development, authentication is optional but recommended.

    Args:
        data: Dictionary containing cleanup options
        authenticated: Authentication dependency (automatically injected)
    """
    try:
        cleanup_memory = data.get("cleanup_memory", True)
        cleanup_files = data.get("cleanup_files", True)
        max_age_hours = data.get("max_age_hours", 24)  # Default: cleanup after 24 hours
        dry_run = data.get("dry_run", False)

        # Validate max_age_hours
        if max_age_hours < 1:
            raise HTTPException(
                status_code=400, detail="max_age_hours must be at least 1 hour."
            )

        if max_age_hours > 8760:  # 1 year in hours
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

        # Clean up memory storage
        if cleanup_memory:
            memory_storage = get_memory_storage()
            memory_items_before = memory_storage.get_size_info()["items_count"]

            if not dry_run:
                memory_storage.clear()  # Clear all memory storage for now
                memory_items_after = 0
            else:
                memory_items_after = memory_items_before

            results["memory_cleanup"] = {
                "items_before": memory_items_before,
                "items_after": memory_items_after,
                "items_cleaned": memory_items_before - memory_items_after,
            }

        # Clean up orphaned temp files and update metadata
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

                        # Check if metadata is old enough and has pending cleanup
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
                                        # Use secure deletion
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

                                # Update metadata
                                if not dry_run:
                                    metadata.pop("temp_content_file", None)
                                    metadata.pop("temp_storage_type", None)
                                    metadata.pop("job_id", None)
                                    metadata["cleanup_completed"] = True
                                    metadata["cleanup_at"] = datetime.now().isoformat()

                                    with open(
                                        metadata_path, "w", encoding="utf-8"
                                    ) as f:
                                        json.dump(metadata, f, indent=2)
                                    metadata_updated += 1

                    except Exception as e:
                        print(
                            f"Warning: Failed to process metadata file {filename}: {e}"
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
        # Re-raise HTTP exceptions (authentication, validation errors)
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Temp storage cleanup failed: {str(e)}"
        ) from e
