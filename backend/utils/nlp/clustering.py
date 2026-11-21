import logging
from typing import Any, Dict, List

from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)

# Handle NLTK stopwords with graceful fallback
try:
    from nltk.corpus import stopwords
    import nltk

    # Try to access stopwords, download if needed
    try:
        stopwords.words("english")
    except LookupError:
        logger.info("Downloading NLTK stopwords corpus...")
        nltk.download("stopwords", quiet=True)
    NLTK_AVAILABLE = True
except ImportError:
    logger.warning("NLTK not available, using sklearn's built-in stopwords")
    NLTK_AVAILABLE = False


def get_stopwords():
    """
    Get English stopwords with fallback options.

    Returns:
        List of stopwords or 'english' string for sklearn built-in stopwords
    """
    if NLTK_AVAILABLE:
        try:
            return stopwords.words("english")
        except LookupError:
            logger.warning(
                "NLTK stopwords not available, using sklearn's built-in stopwords"
            )
            return "english"
    else:
        return "english"


def pre_cluster_with_kmeans(
    chunks: List[Dict[str, str]],
    min_cluster_size: int = 10,
    min_words_per_cluster: int = 500,
) -> List[List[Dict[str, str]]]:
    """
    Use k-means clustering to split chunks into 2 clusters before running BERTopic.
    Only performs clustering if each resulting cluster would have enough content.

    Args:
        chunks: List of chunk dictionaries with 'position' and 'text' keys
        min_cluster_size: Minimum number of chunks required per cluster
        min_words_per_cluster: Minimum number of words required per cluster

    Returns:
        List of chunk clusters. If clustering criteria aren't met, returns [chunks] (single cluster)
    """
    # Check if we have enough chunks to split
    if len(chunks) < min_cluster_size * 2:
        logger.info(
            f"Not enough chunks ({len(chunks)}) for k-means pre-clustering. Need at least {min_cluster_size * 2}."
        )
        return [chunks]

    # Check if we have enough total words
    total_words = sum(len(chunk["text"].split()) for chunk in chunks)
    if total_words < min_words_per_cluster * 2:
        logger.info(
            f"Not enough words ({total_words}) for k-means pre-clustering. Need at least {min_words_per_cluster * 2}."
        )
        return [chunks]

    logger.info(f"Performing k-means pre-clustering on {len(chunks)} chunks...")
    # Extract texts for vectorization
    texts = [chunk["text"] for chunk in chunks]

    # Use TF-IDF vectorization for k-means
    stopword_list = get_stopwords()
    tfidf_vectorizer = TfidfVectorizer(
        stop_words=stopword_list,
        max_features=1000,  # Limit features for efficiency
        max_df=0.95,
        min_df=2,
        ngram_range=(1, 2),
    )

    try:
        # Vectorize texts
        tfidf_matrix = tfidf_vectorizer.fit_transform(texts)

        # Perform k-means clustering with k=2
        kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(tfidf_matrix)

        # Group chunks by cluster
        cluster_0 = []
        cluster_1 = []

        for chunk, label in zip(chunks, cluster_labels):
            if label == 0:
                cluster_0.append(chunk)
            else:
                cluster_1.append(chunk)

        # Calculate cluster statistics
        cluster_0_words = sum(len(chunk["text"].split()) for chunk in cluster_0)
        cluster_1_words = sum(len(chunk["text"].split()) for chunk in cluster_1)

        logger.info("K-means clustering results:")
        logger.info(f"  Cluster 0: {len(cluster_0)} chunks, {cluster_0_words} words")
        logger.info(f"  Cluster 1: {len(cluster_1)} chunks, {cluster_1_words} words")

        # Check if both clusters meet minimum requirements
        if (
            len(cluster_0) >= min_cluster_size
            and cluster_0_words >= min_words_per_cluster
            and len(cluster_1) >= min_cluster_size
            and cluster_1_words >= min_words_per_cluster
        ):
            logger.info(
                "Both clusters meet minimum requirements. Proceeding with split clustering."
            )
            return [cluster_0, cluster_1]

        logger.info(
            "One or both clusters don't meet minimum requirements. Using single cluster."
        )
        return [chunks]

    except Exception as e:
        logger.error(f"K-means clustering failed: {e}. Using single cluster.")
        return [chunks]


def redistribute_large_topics(
    topic_map: Dict[str, List[Dict[str, str]]],
    topic_model: Any,
    cluster_id: int,
    max_topic_percentage: float = 0.6,
) -> Dict[str, List[Dict[str, str]]]:
    """
    Redistribute chunks from overly large topics to smaller topics based on semantic similarity.

    Redistribution Logic:
    - Identify topics exceeding the maximum allowable percentage of total chunks.
    - Calculate the centroid (average vector) for each topic using TF-IDF vectorization.
    - For overly large topics, determine the least similar chunks to the topic's centroid.
    - Redistribute these chunks to the most semantically similar smaller topics based on cosine similarity.
    - Update the topic map with redistributed chunks and print a summary of changes.

    Args:
        topic_map: Dictionary mapping topic IDs to lists of chunks.
        topic_model: The BERTopic model used for this cluster.
        cluster_id: ID of the cluster being processed.
        max_topic_percentage: Maximum percentage of total chunks a single topic should contain.

    Returns:
        Updated topic_map with redistributed chunks.
    """
    if len(topic_map) < 2:
        logger.info(
            f"Cluster {cluster_id}: Only {len(topic_map)} topics, skipping redistribution"
        )
        return topic_map

    # Kept for signature compatibility and future extension.
    _ = topic_model

    # Calculate the total number of chunks across all topics
    total_chunks = sum(len(chunks) for chunks in topic_map.values())

    # Determine the maximum allowable chunks per topic based on the percentage threshold
    max_chunks_per_topic = int(total_chunks * max_topic_percentage)

    # Find overly large topics
    large_topics = {
        tid: chunks
        for tid, chunks in topic_map.items()
        if len(chunks) > max_chunks_per_topic
    }

    if not large_topics:
        logger.info(
            f"Cluster {cluster_id}: No topics exceed {max_topic_percentage*100}% threshold, skipping redistribution"
        )
        return topic_map

    logger.info(
        f"Cluster {cluster_id}: Found {len(large_topics)} large topics requiring redistribution"
    )
    # Import necessary libraries for similarity calculation
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np

    # Get all texts for vectorization
    all_texts = []
    text_to_topic = {}

    for tid, chunks in topic_map.items():
        topic_texts = [chunk["text"] for chunk in chunks]
        for i, text in enumerate(topic_texts):
            all_texts.append(text)
            text_to_topic[len(all_texts) - 1] = (tid, i)

    # Vectorize all texts
    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=500,
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95,
        )
        text_vectors = vectorizer.fit_transform(all_texts)

        # Convert sparse matrix to dense array for easier manipulation
        text_vectors_dense = np.array(text_vectors.todense())

        # Calculate topic centroids (average vector for each topic)
        topic_centroids = {}
        for tid, chunks in topic_map.items():
            topic_indices = [i for i, (t_id, _) in text_to_topic.items() if t_id == tid]
            if topic_indices:
                # Select rows using dense array
                topic_vectors = text_vectors_dense[topic_indices]
                centroid = np.mean(topic_vectors, axis=0)
                topic_centroids[tid] = centroid

        redistributed_map = topic_map.copy()

        for large_tid, large_chunks in large_topics.items():
            # Calculate how many chunks to redistribute
            excess_chunks = len(large_chunks) - max_chunks_per_topic
            logger.info(
                f"  Topic {large_tid}: {len(large_chunks)} chunks, redistributing {excess_chunks}"
            )
            # Get vectors for chunks in this large topic
            large_topic_indices = [
                i for i, (t_id, _) in text_to_topic.items() if t_id == large_tid
            ]
            large_topic_vectors = text_vectors_dense[large_topic_indices]

            # Calculate distance from each chunk to the topic centroid
            large_centroid = topic_centroids[large_tid].reshape(1, -1)
            distances = cosine_similarity(large_topic_vectors, large_centroid).flatten()

            # Sort chunks by distance (farthest first - least similar to topic center)
            chunk_distances = list(zip(large_chunks, distances))
            chunk_distances.sort(
                key=lambda x: x[1]
            )  # Sort by similarity (ascending = least similar first)

            # Select chunks to redistribute (least similar ones)
            chunks_to_redistribute = [
                chunk for chunk, _ in chunk_distances[:excess_chunks]
            ]
            remaining_chunks = [chunk for chunk, _ in chunk_distances[excess_chunks:]]

            # Update the large topic with remaining chunks
            redistributed_map[large_tid] = remaining_chunks

            # Find best topics for each chunk to redistribute
            other_topics = {
                tid: centroid
                for tid, centroid in topic_centroids.items()
                if tid != large_tid
            }

            for chunk in chunks_to_redistribute:
                chunk_text = chunk["text"]
                chunk_vector = vectorizer.transform([chunk_text])

                # Calculate similarity to all other topic centroids
                best_topic = None
                best_similarity = -1

                for other_tid, other_centroid in other_topics.items():
                    similarity = cosine_similarity(
                        chunk_vector, other_centroid.reshape(1, -1)
                    )[0][0]
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_topic = other_tid

                # Add chunk to the most similar topic
                if best_topic:
                    redistributed_map[best_topic].append(chunk)
                    logger.debug(
                        f"    Moved chunk to topic {best_topic} (similarity: {best_similarity:.3f})"
                    )

        # Print redistribution summary
        logger.info(f"Cluster {cluster_id} redistribution summary:")
        for tid, chunks in redistributed_map.items():
            original_count = len(topic_map[tid])
            new_count = len(chunks)
            change = new_count - original_count
            change_str = f"+{change}" if change > 0 else str(change)
            logger.info(
                f"  Topic {tid}: {original_count} -> {new_count} chunks ({change_str})"
            )

        return redistributed_map

    except Exception as e:
        logger.error(f"Cluster {cluster_id}: Error during redistribution: {e}")
        logger.info("Returning original topic map")
        return topic_map