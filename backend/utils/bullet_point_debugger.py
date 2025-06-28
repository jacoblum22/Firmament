import numpy as np
from typing import List, Dict, Union, Any
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

_model_instance = None


def get_model():
    """Lazy-load and cache the SentenceTransformer model."""
    global _model_instance
    if _model_instance is None:
        _model_instance = SentenceTransformer("all-MiniLM-L6-v2")
    return _model_instance


def find_top_similar_chunks(
    bullet_point: str, chunks: List[str], top_k: int = 5
) -> List[Dict[str, Union[str, float]]]:
    """
    Find the top K chunks most similar to a given bullet point.

    Parameters:
    bullet_point (str): The bullet point to analyze.
    chunks (List[str]): The list of chunks in the topic.
    top_k (int): Number of top similar chunks to return (default: 5).

    Returns:
    List[Dict[str, Union[str, float]]]: A list of dictionaries containing the top similar chunks and their similarity scores.
    """
    model = get_model()

    # Encode the bullet point and chunks
    bullet_embedding = model.encode([bullet_point])
    chunk_embeddings = model.encode(chunks)

    # Compute cosine similarities
    similarities = cosine_similarity(bullet_embedding, chunk_embeddings)[0]

    # Get top K most similar chunks
    top_indices = np.argsort(similarities)[::-1][:top_k]

    return [
        {"chunk": chunks[idx], "similarity": similarities[idx]} for idx in top_indices
    ]


def find_most_similar_chunk(
    bullet_point: str, chunks: List[str]
) -> Dict[str, Union[str, float]]:
    """
    Find the chunk most similar to a given bullet point.

    This function is kept for backward compatibility.

    Parameters:
    bullet_point (str): The bullet point to analyze.
    chunks (List[str]): The list of chunks in the topic.

    Returns:
    Dict[str, Union[str, float]]: A dictionary containing the most similar chunk and its similarity score.
    """
    top_chunks = find_top_similar_chunks(bullet_point, chunks, top_k=1)
    return top_chunks[0] if top_chunks else {"chunk": "", "similarity": 0.0}


def compare_chunk_to_topics(
    chunk: str, topics: Dict[str, List[str]]
) -> Dict[str, float]:
    """
    Compare a chunk's similarity to all topics.

    Parameters:
    chunk (str): The chunk to compare.
    topics (Dict[str, List[str]]): A dictionary where keys are topic names and values are lists of chunks.

    Returns:
    Dict[str, float]: A dictionary of topic names and their similarity scores to the chunk.
    """
    # Early return for empty input
    if not chunk or not chunk.strip():
        return {}

    # Early return for no topics
    if not topics:
        return {}

    try:
        model = get_model()

        # Encode the chunk and all topic chunks
        chunk_embedding = model.encode([chunk])
        topic_similarities = {}

        for topic_name, topic_chunks in topics.items():
            # Skip empty topic lists
            if not topic_chunks:
                topic_similarities[topic_name] = 0.0
                continue

            topic_embeddings = model.encode(topic_chunks)
            similarities = cosine_similarity(chunk_embedding, topic_embeddings)[0]
            topic_similarities[topic_name] = np.mean(
                similarities
            )  # Average similarity to the topic

        return topic_similarities

    except Exception as e:
        print(f"Error in compare_chunk_to_topics: {e}")
        return {}


def debug_bullet_point(
    bullet_point: str, chunks: List[str], topics: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Debug a bullet point by finding its top 5 most similar chunks and comparing the most similar chunk to other topics.

    Parameters:
    bullet_point (str): The bullet point to debug.
    chunks (List[str]): The list of chunks in the current topic.
    topics (Dict[str, Dict[str, Any]]): A dictionary of all topics with their metadata and chunks.

    Returns:
    Dict[str, any]: A dictionary containing the top 5 similar chunks, the most similar chunk's similarity to the current topic,
                    and its similarities to other topics (with titles).
    """
    # Find the top 5 most similar chunks in the current topic
    top_similar_chunks = find_top_similar_chunks(bullet_point, chunks, top_k=5)

    # Use the most similar chunk for topic comparison
    most_similar_chunk = top_similar_chunks[0]["chunk"] if top_similar_chunks else ""
    most_similar_similarity = (
        top_similar_chunks[0]["similarity"] if top_similar_chunks else 0.0
    )

    # Compare the most similar chunk to all topics
    topic_similarities = compare_chunk_to_topics(
        str(most_similar_chunk),
        {topic_id: topic_data["examples"] for topic_id, topic_data in topics.items()},
    )

    # Map topic IDs to their titles for the similarities
    topic_similarities_with_titles = {
        topics[topic_id]["heading"]: similarity
        for topic_id, similarity in topic_similarities.items()
    }

    return {
        "bullet_point": bullet_point,
        "top_similar_chunks": top_similar_chunks,
        "most_similar_chunk": most_similar_chunk,
        "similarity_to_current_topic": most_similar_similarity,
        "topic_similarities": topic_similarities_with_titles,
    }
