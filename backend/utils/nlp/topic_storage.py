import json
import logging
import os
from typing import Any, Dict, List, Tuple, cast

logger = logging.getLogger(__name__)

PROCESSED_DIR = "processed"  # Folder to save processed JSON files


def _save_processed_data(
    filename: str,
    chunks: List[Dict[str, str]],
    all_topic_maps: Dict[str, List[Dict[str, str]]],
    all_noise_chunks: List[Dict[str, str]],
    total_tokens: int,
    total_words: int,
    noise_words: int,
    topic_words: int,
    ordered_topic_ids: List[str],
    all_topic_models: List[Tuple[Any, int]],
    cluster_info: List[Dict[str, str]],
    topic_stats: Dict[str, Dict[str, Any]],
    result_topics: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Save processed data to a JSON file and clean up temporary files.

    Args:
        filename: Name of the file to save
        chunks: Original list of chunks
        all_topic_maps: Dictionary mapping topic IDs to lists of chunks
        all_noise_chunks: List of chunks not assigned to any topic
        total_tokens: Total tokens used for processing
        total_words: Total word count
        noise_words: Word count in noise chunks
        topic_words: Word count in topic chunks
        ordered_topic_ids: List of topic IDs in chronological order
        all_topic_models: List of topic models and their cluster IDs
        cluster_info: List of cluster information
        topic_stats: Dictionary of topic statistics
        result_topics: Dictionary of result topics

    Returns:
        Dictionary containing the saved data structure
    """
    logger.info(f"Saving processed data to {PROCESSED_DIR}")
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    base_name = os.path.splitext(filename)[0]
    save_path = os.path.join(PROCESSED_DIR, f"{base_name}_processed.json")
    logger.info(f"Save path: {save_path}")

    # Prepare data for saving - collect all chunks from topics and noise
    all_segments = []
    # Add chunks from topics
    for topic_chunks in all_topic_maps.values():
        all_segments.extend(topic_chunks)
    # Add noise chunks
    all_segments.extend(all_noise_chunks)
    # Sort by position
    all_segments.sort(key=lambda x: x["position"])

    segments_word_count = sum(len(seg["text"].split()) for seg in all_segments)
    logger.info(
        f"Saving {len(all_segments)} segments, {segments_word_count} words (expected {topic_words + noise_words})"
    )

    clusters = []
    for i, tid in enumerate(ordered_topic_ids):
        # Find which topic model this topic belongs to
        topic_model = None
        original_tid = tid

        # Check which cluster this topic came from based on the offset
        for tm, cluster_idx in all_topic_models:
            cluster_offset = cluster_idx * 1000
            if int(tid) >= cluster_offset and int(tid) < (cluster_offset + 1000):
                topic_model = tm
                original_tid = int(tid) - cluster_offset
                break

        # Get topic words if we found the right model
        topic_words_list = []
        if topic_model:
            try:
                raw_topic_words = topic_model.get_topic(original_tid)
                topic_words_list = cast(
                    List[Tuple[str, float]],
                    raw_topic_words if isinstance(raw_topic_words, list) else [],
                )
            except Exception as e:
                logger.warning(
                    "Failed to get topic words for topic %s: %s", original_tid, e
                )
                topic_words_list = []

        clusters.append(
            {
                "cluster_id": tid,
                "heading": cluster_info[i]["heading"],
                "concepts": cluster_info[i]["concepts"],
                "segment_positions": [
                    chunk["position"] for chunk in all_topic_maps[tid]
                ],
                "keywords": [word for word, _ in topic_words_list[:5]],
                "examples": [chunk["text"] for chunk in all_topic_maps[tid][:3]],
                "stats": topic_stats[tid],
                "summary": cluster_info[i]["summary"],
            }
        )

    # --- FIX: Always include segments and meta in the saved file ---
    save_data = {
        "segments": all_segments,  # All original chunks, sorted by position
        "clusters": clusters,
        "meta": {
            "num_chunks": len(chunks),
            "num_topics": len(all_topic_maps),
            "num_noise_chunks": len(all_noise_chunks),
            "total_tokens_used": total_tokens,
            "total_words": total_words,
            "words_in_topics": topic_words,
            "words_in_noise": noise_words,
            "words_in_segments": segments_word_count,
            "kmeans_clusters_used": len(clusters),
        },
        # Also include the top-level topic modeling summary for compatibility
        "num_chunks": len(chunks),
        "num_topics": len(all_topic_maps),
        "total_tokens_used": total_tokens,
        "topics": result_topics,
    }

    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {os.path.getsize(save_path) / 1024:.1f} KB to {save_path}")

    # Attempt to remove original transcript if it exists
    transcript_path = os.path.join("output", f"{base_name}_transcription.txt")
    try:
        if os.path.exists(transcript_path):
            os.remove(transcript_path)
            logger.info(f"Deleted original transcript: {transcript_path}")
    except Exception as e:
        logger.warning(f"Failed to delete original transcript: {e}")

    # Attempt to remove the corresponding _chunks.json file after saving _processed.json
    chunks_path = os.path.join(PROCESSED_DIR, f"{base_name}_chunks.json")
    try:
        if os.path.exists(chunks_path):
            os.remove(chunks_path)
            logger.info(f"Deleted chunk file: {chunks_path}")
    except Exception as e:
        logger.warning(f"Failed to delete chunk file: {e}")

    return save_data