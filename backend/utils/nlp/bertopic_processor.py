import logging
from typing import Any, Dict, List, Optional

from .clustering import pre_cluster_with_kmeans
from .topic_analysis import _process_clusters_with_bertopic
from .topic_formatting import (
    _build_result_topics,
    _calculate_topic_statistics,
    _generate_topic_headings,
    _print_initial_statistics,
    _print_overall_results,
)
from .topic_storage import _save_processed_data

logger = logging.getLogger(__name__)


def process_with_bertopic(
    chunks: List[Dict[str, str]],
    filename: Optional[str] = None,
    api_key: str | None = None,
    base_url_override: str | None = None,
    model_override: str | None = None,
) -> Dict[str, Any]:
    """
    Process chunks using BERTopic to generate topics and analyze them.
    First uses k-means to pre-cluster chunks, then runs BERTopic on each cluster.
    Falls back to single-cluster processing if pre-clustering criteria aren't met.

    Args:
        chunks: List of chunk dictionaries with 'position' and 'text' keys
        filename: Optional filename to save processed data (if None, no file is saved)

    Returns:
        Dictionary containing topic analysis results
    """
    if not chunks:
        logger.error("No chunks provided to process_with_bertopic")
        return {"num_chunks": 0, "num_topics": 0, "total_tokens_used": 0, "topics": {}}

    total_words = _print_initial_statistics(chunks)

    # BERTopic + UMAP require a minimum number of samples to build a meaningful
    # similarity graph.  Below this threshold we skip clustering entirely and
    # treat the full input as a single topic, then let the LLM generate the
    # heading.  This also avoids the slow SentenceTransformer load for tiny files.
    _MIN_CHUNKS_FOR_BERTOPIC = 20
    if len(chunks) < _MIN_CHUNKS_FOR_BERTOPIC:
        logger.info(
            f"Only {len(chunks)} chunk(s) — below minimum ({_MIN_CHUNKS_FOR_BERTOPIC}) "
            "for BERTopic/UMAP. Treating entire input as a single topic."
        )
        all_topic_maps: dict = {0: list(chunks)}
        all_noise_chunks: list = []
        all_topic_models: list = []
    else:
        clusters = pre_cluster_with_kmeans(chunks)

        logger.info(f"K-Means Clustering Results: {len(clusters)} groups")
        for i, cluster in enumerate(clusters):
            cluster_words = sum(len(chunk["text"].split()) for chunk in cluster)
            logger.info(f"  Group {i}: {len(cluster)} chunks, {cluster_words} words")

        all_topic_maps, all_noise_chunks, all_topic_models = _process_clusters_with_bertopic(
            clusters
        )
    # `clusters` only exists in the BERTopic path; reconstruct a surrogate for logging
    _clusters_for_log = list(all_topic_maps.values()) + ([all_noise_chunks] if all_noise_chunks else [])
    noise_words, topic_words = _print_overall_results(
        _clusters_for_log, all_topic_maps, all_noise_chunks
    )

    ordered_topic_ids, topic_chunks_list, cluster_info, total_tokens = _generate_topic_headings(
        all_topic_maps,
        api_key=api_key,
        base_url_override=base_url_override,
        model_override=model_override,
    )
    _ = topic_chunks_list

    topic_stats = _calculate_topic_statistics(ordered_topic_ids, all_topic_maps)
    result_topics = _build_result_topics(
        ordered_topic_ids, all_topic_maps, all_topic_models, cluster_info, topic_stats
    )

    all_segments = []
    for topic_chunks in all_topic_maps.values():
        all_segments.extend(topic_chunks)
    all_segments.extend(all_noise_chunks)
    all_segments.sort(key=lambda x: x["position"])

    result = {
        "num_chunks": len(chunks),
        "num_topics": len(all_topic_maps),
        "total_tokens_used": total_tokens,
        "segments": all_segments,
        "topics": result_topics,
    }

    if filename:
        return _save_processed_data(
            filename,
            chunks,
            all_topic_maps,
            all_noise_chunks,
            total_tokens,
            total_words,
            noise_words,
            topic_words,
            ordered_topic_ids,
            all_topic_models,
            cluster_info,
            topic_stats,
            result_topics,
        )

    return result
