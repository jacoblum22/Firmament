import json
import logging
import os
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from utils.storage.content_cache import get_content_cache
from utils.common.error_messages import ErrorMessages
from utils.storage.secure_temp_files import SecureTempFile, get_memory_storage

from .constants import OUTPUT_DIR, PROCESSED_DIR
from .health import get_llm_api_key

logger = logging.getLogger(__name__)

router = APIRouter(tags=["processing"])


def get_semantic_segment():
    try:
        from utils.nlp.semantic_segmentation import semantic_segment

        return semantic_segment
    except ImportError as import_error:
        logger.warning(
            "Falling back to basic semantic segmentation due to import failure: %s",
            import_error,
        )

        def semantic_segment(text, similarity_threshold=0.3):
            return [{"start": 0, "end": len(text), "text": text}]

        return semantic_segment


def get_filter_chunks():
    try:
        from utils.nlp.filter_chunks import filter_chunks

        return filter_chunks
    except ImportError as import_error:
        logger.warning(
            "Falling back to pass-through chunk filtering due to import failure: %s",
            import_error,
        )

        def filter_chunks(chunks, min_words=5, max_stopword_ratio=0.9):
            return chunks

        return filter_chunks


def get_optimize_chunk_sizes():
    try:
        from utils.nlp.chunk_size_optimizer import optimize_chunk_sizes

        return optimize_chunk_sizes
    except ImportError as import_error:
        logger.warning(
            "Falling back to unoptimized chunk sizes due to import failure: %s",
            import_error,
        )

        def optimize_chunk_sizes(chunks, min_words=50, max_words=150, target_size=100):
            return chunks

        return optimize_chunk_sizes


def get_bertopic_processor():
    try:
        from utils.nlp.bertopic_processor import process_with_bertopic

        return process_with_bertopic
    except ImportError as import_error:
        logger.warning(
            "Falling back to empty BERTopic output due to import failure: %s",
            import_error,
        )

        def process_with_bertopic(chunks, filename=None, api_key=None):
            return {
                "topics": {},
                "num_chunks": len(chunks),
                "num_topics": 0,
                "total_tokens_used": 0,
            }

        return process_with_bertopic


@router.post("/test-bertopic")
def test_bertopic(data: dict, llm_overrides: dict = Depends(get_llm_api_key)):
    text = data.get("text", "")
    full_filename = data.get("filename") or "default"
    filename = os.path.splitext(full_filename)[0]

    semantic_segment = get_semantic_segment()
    filter_chunks = get_filter_chunks()
    optimize_chunk_sizes = get_optimize_chunk_sizes()
    process_with_bertopic = get_bertopic_processor()

    raw_chunks = semantic_segment(text, similarity_threshold=0.5)
    filtered_chunks = filter_chunks(raw_chunks, min_words=4, max_stopword_ratio=0.75)
    chunks = optimize_chunk_sizes(
        filtered_chunks, min_words=75, max_words=150, target_size=125
    )

    result = process_with_bertopic(
        chunks,
        filename,
        api_key=llm_overrides.get("api_key"),
        base_url_override=llm_overrides.get("base_url"),
        model_override=llm_overrides.get("model"),
    )

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
    processing_id = data.get("processing_id")
    filename = processing_id or os.path.splitext(full_filename)[0]

    semantic_segment = get_semantic_segment()
    filter_chunks = get_filter_chunks()
    optimize_chunk_sizes = get_optimize_chunk_sizes()

    raw_chunks = semantic_segment(text, similarity_threshold=0.5)
    filtered_chunks = filter_chunks(raw_chunks, min_words=4, max_stopword_ratio=0.75)
    chunks = optimize_chunk_sizes(
        filtered_chunks, min_words=50, max_words=100, target_size=75
    )

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

    second_min_words = min_words
    if len(word_counts) >= 2:
        sorted_counts = sorted(word_counts)
        second_min_words = sorted_counts[1]

    logger.info(
        f"Chunking '{filename}': {len(chunks)} chunks, "
        f"second-min: {second_min_words}, max: {max_words}, avg: {avg_words}"
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
def generate_headings(data: dict, llm_overrides: dict = Depends(get_llm_api_key)):
    full_filename = data.get("filename")
    processing_id = data.get("processing_id")
    if not full_filename and not processing_id:
        return JSONResponse(
            status_code=400,
            content={"error": "Filename or processing_id is required."},
        )
    filename = processing_id or os.path.splitext(full_filename)[0]

    chunk_file = os.path.join(PROCESSED_DIR, f"{filename}_chunks.json")
    processed_file = os.path.join(PROCESSED_DIR, f"{filename}_processed.json")
    chunks = []
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
        return JSONResponse(status_code=404, content=error_info)

    if not chunks:
        error_info = ErrorMessages.get_user_friendly_error(
            "file_not_found",
            f"No chunks found for filename: {filename}",
            {"filename": filename},
        )
        return JSONResponse(status_code=404, content=error_info)

    process_with_bertopic = get_bertopic_processor()
    try:
        result = process_with_bertopic(
            chunks,
            filename,
            api_key=llm_overrides.get("api_key"),
            base_url_override=llm_overrides.get("base_url"),
            model_override=llm_overrides.get("model"),
        )
    except Exception as processing_error:
        logger.exception(
            "BERTopic / topic heading generation failed for filename=%s",
            filename,
        )
        error_info = ErrorMessages.get_user_friendly_error(
            "processing_failed",
            str(processing_error),
            {"filename": filename},
        )
        return JSONResponse(status_code=500, content=error_info)

    processed_path = os.path.join(PROCESSED_DIR, f"{filename}_processed.json")
    with open(processed_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    metadata_file = os.path.join(OUTPUT_DIR, f"{filename}_metadata.json")
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            temp_content_file = metadata.get("temp_content_file")
            content_hash = metadata.get("content_hash")
            original_filename = metadata.get("original_filename", full_filename)
            temp_storage_type = metadata.get("temp_storage_type", "legacy")
            job_id = metadata.get("job_id")

            file_bytes = None

            if temp_storage_type == "memory" and content_hash and job_id:
                memory_storage = get_memory_storage()
                file_bytes = memory_storage.retrieve(f"{job_id}_{content_hash}")
                if file_bytes:
                    logger.info(
                        f"Retrieved file content from secure memory storage (hash: {content_hash[:8]}...)"
                    )
                else:
                    logger.warning(
                        "File content not found in memory storage, may have been cleaned up"
                    )

            elif (
                temp_storage_type == "secure_temp"
                and temp_content_file
                and os.path.exists(temp_content_file)
            ):
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
                try:
                    with open(temp_content_file, "rb") as f:
                        file_bytes = f.read()
                    logger.info(
                        f"Retrieved file content from legacy temp file (hash: {content_hash[:8]}...)"
                    )
                except Exception as read_error:
                    logger.warning(
                        f"Failed to read legacy temp file {temp_content_file}: {read_error}"
                    )

            if file_bytes and content_hash:
                cache = get_content_cache()
                try:
                    saved_hash = cache.save_processed_cache(
                        file_bytes, result, original_filename
                    )
                    logger.info(
                        f"Saved processed data to content cache (hash: {saved_hash[:8]}...)"
                    )
                except Exception as cache_error:
                    logger.warning(
                        f"Failed to save processed data to cache: {cache_error}"
                    )

                try:
                    if temp_storage_type == "memory" and job_id:
                        memory_storage = get_memory_storage()
                        if memory_storage.remove(f"{job_id}_{content_hash}"):
                            logger.info(f"Cleaned up memory storage for job {job_id}")
                    elif temp_content_file and os.path.exists(temp_content_file):
                        temp_manager = SecureTempFile(secure_delete=True)
                        if temp_manager.cleanup_file(temp_content_file):
                            logger.info(
                                f"Securely cleaned up temporary content file: {temp_content_file}"
                            )
                        else:
                            os.remove(temp_content_file)
                            logger.info(
                                f"Cleaned up temporary content file (fallback): {temp_content_file}"
                            )
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up temp storage: {cleanup_error}")

                metadata.pop("temp_content_file", None)
                metadata.pop("temp_storage_type", None)
                metadata.pop("job_id", None)
                metadata["cached_at"] = datetime.now().isoformat()
                metadata["cleanup_completed"] = True
                with open(metadata_file, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, indent=2)

        except Exception as e:
            logger.warning(
                f"Failed to process content cache during topic generation: {e}"
            )

    return {
        "message": "Topics generated successfully.",
        "num_topics": result["num_topics"],
        "num_chunks": result.get("num_chunks", 0),
        "total_tokens_used": result.get("total_tokens_used", 0),
        "segments": result.get("segments", chunks),
        "topics": result["topics"],
    }

