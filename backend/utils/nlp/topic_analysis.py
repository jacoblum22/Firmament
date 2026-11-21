import logging
from typing import Any, Dict, List, Tuple

from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer
from umap import UMAP

from .clustering import get_stopwords, redistribute_large_topics

logger = logging.getLogger(__name__)

# UMAP requires at least n_neighbors+1 samples; below this threshold we bypass
# BERTopic entirely and treat all chunks as a single topic to avoid the
# "zero-size array" crash and eliminate unnecessary model-loading time.
_BERTOPIC_MIN_CHUNKS = 5


def _single_topic_result(
    cluster_chunks: List[Dict[str, str]], cluster_id: int
) -> Tuple[Dict[str, List[Dict[str, str]]], List[Dict[str, str]], None]:
    """Return all chunks as a single dummy topic without running BERTopic."""
    topic_id = cluster_id * 1000
    topic_map = {topic_id: list(cluster_chunks)}
    logger.info(
        f"Cluster {cluster_id}: only {len(cluster_chunks)} chunk(s) — "
        f"skipping BERTopic, treating as single topic {topic_id}."
    )
    return topic_map, [], None


def process_cluster_with_bertopic(
    cluster_chunks: List[Dict[str, str]], cluster_id: int
) -> Tuple[Dict[str, List[Dict[str, str]]], List[Dict[str, str]], Any]:
    """
    Process a single cluster of chunks with BERTopic.

    Args:
        cluster_chunks: List of chunks in this cluster
        cluster_id: ID for this cluster (for logging)

    Returns:
        Tuple of (topic_map, noise_chunks, topic_model_or_None)
    """
    logger.info(f"Processing Cluster {cluster_id}")
    logger.info(f"Chunks in cluster: {len(cluster_chunks)}")

    texts = [chunk["text"] for chunk in cluster_chunks]

    # Short-circuit: too few documents for UMAP to build a meaningful graph.
    if len(texts) < _BERTOPIC_MIN_CHUNKS:
        return _single_topic_result(cluster_chunks, cluster_id)

    # Configure vectorizer
    stopword_list = get_stopwords()

    # Calculate dynamic min_topic_size based on cluster size
    # Aim for ~1/5 of chunks, with min=2 and max=10
    dynamic_min_topic_size = max(2, min(10, len(cluster_chunks) // 5))
    logger.info(
        f"Using min_topic_size: {dynamic_min_topic_size} (based on {len(cluster_chunks)} chunks)"
    )

    # Scale UMAP parameters to the actual document count.
    # Rules:
    #   n_neighbors  < n_samples  (hard UMAP requirement)
    #   n_components < n_samples  (spectral init needs k < N where k = n_components+1)
    # Using init="random" skips scipy.eigsh entirely, which avoids the
    # "k >= N" TypeError that fires even when n_components is correctly bounded.
    n_neighbors = max(2, min(15, len(texts) - 1))
    n_components = max(2, min(5, len(texts) - 2))  # -2 so n_components+1 < n_samples
    umap_model = UMAP(
        n_neighbors=n_neighbors,
        n_components=n_components,
        metric="cosine",
        init="random",          # avoids spectral init → no scipy.eigsh dependency
        random_state=42,
        low_memory=False,
    )

    # Try with original parameters first
    try:
        vectorizer_model = CountVectorizer(
            stop_words=stopword_list,
            min_df=2,
            max_df=0.95,
            ngram_range=(1, 2),  # Include both unigrams and bigrams
        )

        # Configure embedding model with explicit device handling
        # This fixes PyTorch 2.7+ meta tensor compatibility issues
        embedding_model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2",
            device="cpu",
            model_kwargs={"low_cpu_mem_usage": False},
        )

        # Configure BERTopic
        topic_model = BERTopic(
            embedding_model=embedding_model,
            umap_model=umap_model,
            vectorizer_model=vectorizer_model,
            min_topic_size=dynamic_min_topic_size,  # Dynamic minimum based on cluster size
            nr_topics="auto",  # Automatically determine number of topics
            calculate_probabilities=True,
            verbose=True,
        )

        # Fit the model
        topics, probs = topic_model.fit_transform(texts)

    except (ValueError, TypeError) as e:
        if (
            "max_df corresponds to < documents than min_df" in str(e)
            or "k >= N" in str(e)
            or "zero-size array" in str(e)
        ):
            logger.info(
                f"Falling back to lenient parameters for cluster {cluster_id}..."
            )
            # Fall back to lenient parameters
            vectorizer_model = CountVectorizer(
                stop_words=stopword_list,
                min_df=1,  # More lenient minimum document frequency
                max_df=0.95,
                ngram_range=(1, 2),
            )

            # Configure embedding model with explicit device handling for fallback
            embedding_model_fallback = SentenceTransformer(
                "sentence-transformers/all-MiniLM-L6-v2",
                device="cpu",
                model_kwargs={"low_cpu_mem_usage": False},
            )

            # Re-create a fresh umap_model for the retry
            umap_model_retry = UMAP(
                n_neighbors=n_neighbors,
                n_components=n_components,
                metric="cosine",
                init="random",
                random_state=42,
                low_memory=False,
            )

            topic_model = BERTopic(
                embedding_model=embedding_model_fallback,
                umap_model=umap_model_retry,
                vectorizer_model=vectorizer_model,
                min_topic_size=2,
                nr_topics="auto",
                calculate_probabilities=True,
                verbose=True,
            )

            topics, probs = topic_model.fit_transform(texts)
        else:
            logger.warning(
                f"Unhandled error in BERTopic for cluster {cluster_id} "
                f"({type(e).__name__}: {e}). Falling back to single topic."
            )
            return _single_topic_result(cluster_chunks, cluster_id)

    _ = probs

    # Extract topic-to-chunks mapping
    topic_map = {}
    noise_chunks = []  # Track chunks that weren't assigned to any topic
    for chunk, topic_id in zip(cluster_chunks, topics):
        if topic_id == -1:
            noise_chunks.append(chunk)  # Store noise chunks separately
        else:
            # Offset topic IDs by cluster to avoid conflicts
            adjusted_topic_id = topic_id + (
                cluster_id * 1000
            )  # Large offset to avoid conflicts
            topic_map.setdefault(adjusted_topic_id, []).append(
                chunk
            )  # Print topic assignment stats for this cluster
    logger.info(f"Cluster {cluster_id} topic assignment stats:")
    logger.info(f"  Number of topics found: {len(topic_map)}")
    logger.info(f"  Number of noise chunks: {len(noise_chunks)}")
    logger.info(
        f"  Number of chunks assigned to topics: {sum(len(chunks) for chunks in topic_map.values())}"
    )

    # Redistribute overly large topics
    if len(topic_map) > 1:  # Only redistribute if we have multiple topics
        topic_map = redistribute_large_topics(topic_map, topic_model, cluster_id)

    return topic_map, noise_chunks, topic_model


def _process_clusters_with_bertopic(
    clusters: List[List[Dict[str, str]]],
) -> Tuple[
    Dict[str, List[Dict[str, str]]], List[Dict[str, str]], List[Tuple[Any, int]]
]:
    """
    Process each cluster with BERTopic and collect results.

    Args:
        clusters: List of chunk clusters

    Returns:
        Tuple of (all_topic_maps, all_noise_chunks, all_topic_models)
    """
    all_topic_maps = {}
    all_noise_chunks = []
    all_topic_models = []
    cluster_topic_counts = []  # Track topics per cluster

    for cluster_idx, cluster_chunks in enumerate(clusters):
        topic_map, noise_chunks, topic_model = process_cluster_with_bertopic(
            cluster_chunks, cluster_idx
        )

        # Count topics in this cluster
        cluster_topics = len(
            [
                tid
                for tid in topic_map.keys()
                if int(tid) >= cluster_idx * 1000
                and int(tid) < (cluster_idx + 1) * 1000
            ]
        )
        cluster_topic_counts.append(cluster_topics)
        logger.info(f"Group {cluster_idx} -> Generated {cluster_topics} topics")

        all_topic_maps.update(topic_map)
        all_noise_chunks.extend(noise_chunks)
        # topic_model is None when the short-circuit path was taken (too few chunks)
        if topic_model is not None:
            all_topic_models.append((topic_model, cluster_idx))

    # Print detailed clustering summary
    logger.info(f"Clustering Summary: {len(clusters)} k-means groups")
    for i, count in enumerate(cluster_topic_counts):
        logger.info(f"  Group {i}: {count} topics")
    logger.info(f"Total topics across all groups: {sum(cluster_topic_counts)}")

    return all_topic_maps, all_noise_chunks, all_topic_models