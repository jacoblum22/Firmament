import re
import numpy as np
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

_model_instance = None


def get_model():
    """Lazy-load and cache the SentenceTransformer model."""
    global _model_instance
    if _model_instance is None:
        _model_instance = SentenceTransformer("all-MiniLM-L6-v2")
    return _model_instance


def semantic_segment(
    text: str, similarity_threshold: float = 0.3
) -> List[Dict[str, str]]:
    """
    Segments a given text into semantic blocks based on sentence similarity.

    Parameters:
    text (str): The input text to be segmented.
    similarity_threshold (float): The threshold below which sentences are considered dissimilar enough to start a new segment.

    Returns:
    List[Dict[str, str]]: A list of dictionaries, each containing:
        - "position" (str): The index of the segment.
        - "text" (str): The text content of the segment.
    """
    model = get_model()  # Use the lazy-loaded model

    # Step 1: Split into sentences
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    if len(sentences) < 2:
        return [{"position": "0", "text": text.strip()}]  # Not enough to segment

    # Step 2: Embed each sentence
    embeddings = model.encode(sentences)

    # Step 3: Compute adjacent similarities
    window = 1  # number of sentences per block
    block_embeddings = []

    # Build overlapping blocks
    for i in range(len(sentences) - window + 1):
        # Since window=1, each block is a single sentence, use precomputed embeddings
        block_embeddings.append(embeddings[i])

    # Compare each block to the next one
    similarities = []
    similarity_matrix = cosine_similarity(np.array(block_embeddings))
    similarities = [
        similarity_matrix[i, i + 1] for i in range(len(block_embeddings) - 1)
    ]

    # Step 4: Segment when similarity drops below threshold
    segments = []
    current_segment = sentences[:window]

    for i in range(window, len(sentences)):
        similarity = similarities[i - window]
        if similarity < similarity_threshold:
            segments.append(" ".join(current_segment).strip())
            current_segment = [sentences[i]]
        else:
            current_segment.append(sentences[i])

    if current_segment:
        segments.append(" ".join(current_segment).strip())

    return [{"position": str(i), "text": segment} for i, segment in enumerate(segments)]
