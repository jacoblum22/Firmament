import logging
import statistics
from typing import Any, Dict, List, Tuple, cast

from .generate_cluster_heading import generate_cluster_headings

logger = logging.getLogger(__name__)


def _print_initial_statistics(chunks: List[Dict[str, str]]) -> int:
    """
    Print initial statistics about the chunks to be processed.

    Args:
        chunks: List of chunk dictionaries

    Returns:
        Total word count across all chunks
    """
    total_words = sum(len(chunk["text"].split()) for chunk in chunks)
    logger.info(
        f"Initial stats: {len(chunks)} chunks, {total_words} total words, {total_words/len(chunks):.1f} avg words/chunk"
    )
    return total_words


def _print_overall_results(
    clusters: List[List[Dict[str, str]]],
    all_topic_maps: Dict[str, List[Dict[str, str]]],
    all_noise_chunks: List[Dict[str, str]],
) -> Tuple[int, int]:
    """
    Print overall processing results and word count statistics.

    Args:
        clusters: List of chunk clusters
        all_topic_maps: Dictionary mapping topic IDs to lists of chunks
        all_noise_chunks: List of chunks not assigned to any topic

    Returns:
        Tuple of (noise_words, topic_words)
    """
    total_topics = len(all_topic_maps)
    total_noise = len(all_noise_chunks)
    total_assigned = sum(len(chunks) for chunks in all_topic_maps.values())

    logger.info(
        f"Overall Results: {len(clusters)} clusters, {total_topics} topics, {total_noise} noise, {total_assigned} assigned"
    )

    # Print word counts for noise vs topic chunks
    noise_words = sum(len(chunk["text"].split()) for chunk in all_noise_chunks)
    topic_words = sum(
        len(chunk["text"].split())
        for chunks in all_topic_maps.values()
        for chunk in chunks
    )
    logger.info(
        f"Words: {noise_words} noise, {topic_words} topic, {noise_words + topic_words} total"
    )

    return noise_words, topic_words


def _generate_topic_headings(
    all_topic_maps: Dict[str, List[Dict[str, str]]],
    api_key: str | None = None,
    base_url_override: str | None = None,
    model_override: str | None = None,
) -> Tuple[List[str], List[List[Dict[str, str]]], List[Dict[str, str]], int]:
    """
    Generate topic headings and organize topic data.

    Args:
        all_topic_maps: Dictionary mapping topic IDs to lists of chunks

    Returns:
        Tuple of (ordered_topic_ids, topic_chunks_list, cluster_info, total_tokens)
    """
    # Get all topics in chronological order
    ordered_topic_ids = order_topics_chronologically(all_topic_maps)
    topic_chunks_list = [all_topic_maps[tid] for tid in ordered_topic_ids]

    headings_data: List[Dict[str, str]]
    headings_data, total_tokens = generate_cluster_headings(
        [[chunk["text"] for chunk in cluster] for cluster in topic_chunks_list],
        api_key=api_key,
        base_url_override=base_url_override,
        model_override=model_override,
    )

    # Parse concepts and headings from the response
    cluster_info = []
    for i in range(len(topic_chunks_list)):
        # Handle concepts that might have brackets or other formatting
        concepts_raw = headings_data[i]["concept"]
        # Remove brackets and split by comma
        concepts_clean = concepts_raw.strip("[]").replace("[", "").replace("]", "")
        concepts_list = [c.strip() for c in concepts_clean.split(",") if c.strip()]

        cluster_info.append(
            {
                "concepts": concepts_list,
                "heading": headings_data[i]["heading"],
                "summary": headings_data[i]["summary"],
            }
        )

    return ordered_topic_ids, topic_chunks_list, cluster_info, total_tokens


def _calculate_topic_statistics(
    ordered_topic_ids: List[str], all_topic_maps: Dict[str, List[Dict[str, str]]]
) -> Dict[str, Dict[str, Any]]:
    """
    Calculate and print statistics for each topic.

    Args:
        ordered_topic_ids: List of topic IDs in chronological order
        all_topic_maps: Dictionary mapping topic IDs to lists of chunks

    Returns:
        Dictionary of topic statistics
    """
    topic_stats = {}
    for i, tid in enumerate(ordered_topic_ids):
        _ = i
        topic_chunks = all_topic_maps[tid]
        chunk_sizes = [len(chunk["text"].split()) for chunk in topic_chunks]
        topic_stats[tid] = {
            "num_chunks": len(topic_chunks),
            "min_size": min(chunk_sizes),
            "mean_size": round(statistics.mean(chunk_sizes), 1),
            "max_size": max(chunk_sizes),
        }

    # Print topic statistics
    for tid, stats in topic_stats.items():
        logger.info(
            f"Topic {tid}: {stats['num_chunks']} chunks, "
            f"words {stats['min_size']}-{stats['max_size']} (avg {stats['mean_size']})"
        )

    return topic_stats


def _build_result_topics(
    ordered_topic_ids: List[str],
    all_topic_maps: Dict[str, List[Dict[str, str]]],
    all_topic_models: List[Tuple[Any, int]],
    cluster_info: List[Dict[str, str]],
    topic_stats: Dict[str, Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """
    Build the result topics dictionary with all topic information.

    Args:
        ordered_topic_ids: List of topic IDs in chronological order
        all_topic_maps: Dictionary mapping topic IDs to lists of chunks
        all_topic_models: List of topic models and their cluster IDs
        cluster_info: List of cluster information (concepts, headings, summaries)
        topic_stats: Dictionary of topic statistics

    Returns:
        Dictionary of result topics
    """
    result_topics = {}

    # Build result topics from all clusters
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

        result_topics[str(tid)] = {
            "concepts": cluster_info[i]["concepts"],
            "heading": cluster_info[i]["heading"],
            "summary": cluster_info[i]["summary"],
            "keywords": [word for word, _ in topic_words_list[:5]],
            "examples": [chunk["text"] for chunk in all_topic_maps[tid][:3]],
            "segment_positions": [chunk["position"] for chunk in all_topic_maps[tid]],
            "stats": topic_stats[tid],
        }

    return result_topics


def order_topics_chronologically(
    all_topic_maps: Dict[str, List[Dict[str, str]]],
) -> List[str]:
    """
    Order topics chronologically based on the timestamp/position metadata of their most important chunks.

    This function improves the user experience by ordering topics according to their natural progression
    in the original content, rather than by arbitrary topic IDs. This ensures that:
    - Topics follow the logical flow of the original lecture/document
    - Students can read topics in the order they were presented
    - The content maintains its intended pedagogical structure
    - Related concepts appear in their proper sequence

    The function determines the "importance" of chunks within each topic by their position within the topic
    (assuming BERTopic places more representative chunks first) and orders topics by the earliest
    position of the most important chunks.

    Args:
        all_topic_maps: Dictionary mapping topic IDs to lists of chunks

    Returns:
        List of topic IDs ordered chronologically

    Example:
        >>> topic_maps = {
        ...     "1000": [{"position": "45", "text": "later content"}],
        ...     "1001": [{"position": "10", "text": "early content"}]
        ... }
        >>> order_topics_chronologically(topic_maps)
        ['1001', '1000']  # 1001 comes first because position 10 < 45
    """
    topic_min_positions = {}

    for tid, chunks in all_topic_maps.items():
        if not chunks:
            topic_min_positions[tid] = float("inf")
            continue

        # Get positions as integers for proper sorting
        # Take the first few chunks as they are most representative of the topic
        num_important_chunks = min(
            3, len(chunks)
        )  # Use top 3 most representative chunks
        important_chunks = chunks[:num_important_chunks]

        # Convert positions to integers and find the minimum
        positions = []
        for chunk in important_chunks:
            try:
                position = int(chunk["position"])
                positions.append(position)
            except (ValueError, KeyError):
                # If position is not a valid integer, skip this chunk
                continue

        if positions:
            # Use the earliest position among the important chunks
            topic_min_positions[tid] = min(positions)
        else:
            # If no valid positions found, put at the end
            topic_min_positions[tid] = float("inf")

    # Sort topics by their minimum position (chronological order)
    ordered_topic_ids = sorted(
        all_topic_maps.keys(), key=lambda tid: topic_min_positions[tid]
    )

    logger.info("Topic chronological ordering:")
    for i, tid in enumerate(ordered_topic_ids):
        min_pos = topic_min_positions[tid]
        chunk_count = len(all_topic_maps[tid])
        if min_pos == float("inf"):
            logger.info(
                f"  {i+1}. Topic {tid}: No valid positions, {chunk_count} chunks"
            )
        else:
            logger.info(
                f"  {i+1}. Topic {tid}: Starting at position {min_pos}, {chunk_count} chunks"
            )

    return ordered_topic_ids
