from typing import List, Tuple, Dict
import re
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import queue
import os
import logging

# Initialize a threading lock for model access
model_lock = threading.Lock()
shared_model = None


def get_shared_model() -> SentenceTransformer:
    """Get the shared SentenceTransformer model, initializing it lazily."""
    global shared_model

    with model_lock:
        if shared_model is None:
            try:
                shared_model = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception as e:
                logging.error(f"Failed to initialize SentenceTransformer model: {e}")
                raise

    return shared_model


def get_word_count(chunk: Dict[str, str]) -> int:
    """Get the number of words in a chunk's text."""
    return len(chunk["text"].split())


def get_chunk_similarity(chunk1: Dict[str, str], chunk2: Dict[str, str]) -> float:
    """Calculate semantic similarity between two chunks."""
    model = get_shared_model()
    with model_lock:
        embeddings = model.encode([chunk1["text"], chunk2["text"]])
        emb1 = np.array(embeddings[0]).reshape(1, -1)
        emb2 = np.array(embeddings[1]).reshape(1, -1)
    return cosine_similarity(emb1, emb2)[0][0]


def calculate_similarities(
    chunks: List[Dict[str, str]], start_idx: int, end_idx: int, max_words: int
) -> List[Tuple[int, float]]:
    """Calculate similarities for a range of adjacent chunks."""
    similarities = []
    for i in range(start_idx, min(end_idx, len(chunks) - 1)):
        combined_size = get_word_count(chunks[i]) + get_word_count(chunks[i + 1])
        if combined_size <= max_words:
            similarity = get_chunk_similarity(chunks[i], chunks[i + 1])
            similarities.append((i, similarity))
    return similarities


def split_large_chunk(chunk: Dict[str, str], max_words: int) -> List[Dict[str, str]]:
    """Split a chunk that's too large into smaller chunks."""
    # Try sentence-based splitting first
    sentences = re.split(r"(?<=[.!?])\s+", chunk["text"])

    if len(sentences) > 1:
        # Use sentence boundaries
        result_chunks = []
        current_part = []
        current_size = 0

        for sentence in sentences:
            sentence_size = len(sentence.split())
            if current_size + sentence_size <= max_words:
                current_part.append(sentence)
                current_size += sentence_size
            else:
                if current_part:
                    result_chunks.append(
                        {"position": chunk["position"], "text": " ".join(current_part)}
                    )
                current_part = [sentence]
                current_size = sentence_size

        if current_part:
            result_chunks.append(
                {"position": chunk["position"], "text": " ".join(current_part)}
            )

        return result_chunks
    else:
        # No sentence boundaries, split by word count
        words = chunk["text"].split()
        result_chunks = []

        for i in range(0, len(words), max_words):
            chunk_words = words[i : i + max_words]
            result_chunks.append(
                {"position": chunk["position"], "text": " ".join(chunk_words)}
            )

        return result_chunks


def optimize_chunk_sizes(
    chunks: List[Dict[str, str]],
    min_words: int = 50,
    max_words: int = 100,
    target_size: int = 75,
) -> List[Dict[str, str]]:
    """
    Optimize chunk sizes using a two-phase approach:
    1. Combine undersized chunks (below min_words) with adjacent chunks
    2. Use dendrogram-style merging of adjacent chunks based on semantic similarity

    Args:
        chunks: List of chunk dictionaries with 'position' and 'text' keys
        min_words: Minimum number of words per chunk
        max_words: Maximum number of words per chunk
        target_size: Target number of words per chunk

    Returns:
        List of optimized chunk dictionaries
    """
    if not chunks:
        return []

    # Phase 1: Fix undersized chunks
    current_chunks = chunks.copy()
    i = 0
    while i < len(current_chunks):
        current_size = get_word_count(current_chunks[i])

        # If chunk is too small and not the last chunk
        if current_size < min_words and i < len(current_chunks) - 1:
            next_size = get_word_count(current_chunks[i + 1])
            combined_size = current_size + next_size

            # Only merge if combined size is under max_words
            if combined_size <= max_words:
                current_chunks[i] = {
                    "position": current_chunks[i]["position"],
                    "text": current_chunks[i]["text"]
                    + " "
                    + current_chunks[i + 1]["text"],
                }
                current_chunks.pop(i + 1)
            else:
                i += 1
        else:
            i += 1

    # Phase 2: Dendrogram-style merging with parallel processing
    while True:
        # Calculate current mean chunk size
        chunk_sizes = [get_word_count(chunk) for chunk in current_chunks]
        if not chunk_sizes:
            break
        mean_size = sum(chunk_sizes) / len(chunk_sizes)

        # If we've reached target size, stop
        if mean_size >= target_size:
            break

        # Calculate similarities in parallel
        num_chunks = len(current_chunks)
        if num_chunks <= 1:
            break

        chunk_size = max(1, num_chunks // (os.cpu_count() or 1))
        all_similarities = []

        with ThreadPoolExecutor() as executor:
            futures = []
            for i in range(0, num_chunks - 1, chunk_size):
                end_idx = min(i + chunk_size, num_chunks - 1)
                futures.append(
                    executor.submit(
                        calculate_similarities, current_chunks, i, end_idx, max_words
                    )
                )

            for future in as_completed(futures):
                all_similarities.extend(future.result())

        # Find the best pair to merge
        if not all_similarities:
            break

        best_pair_idx = max(all_similarities, key=lambda x: x[1])[0]

        # Only merge if the combined chunk will be at least min_words
        combined_size = get_word_count(current_chunks[best_pair_idx]) + get_word_count(
            current_chunks[best_pair_idx + 1]
        )
        if combined_size >= min_words:
            current_chunks[best_pair_idx] = {
                "position": current_chunks[best_pair_idx]["position"],
                "text": current_chunks[best_pair_idx]["text"]
                + " "
                + current_chunks[best_pair_idx + 1]["text"],
            }
            current_chunks.pop(best_pair_idx + 1)
        else:
            break

    # Phase 3: Final cleanup - handle oversized and undersized chunks
    final_chunks = []

    # First pass: split any oversized chunks
    for chunk in current_chunks:
        chunk_size = get_word_count(chunk)
        if chunk_size > max_words:
            final_chunks.extend(split_large_chunk(chunk, max_words))
        else:
            final_chunks.append(chunk)

    # Second pass: merge undersized chunks
    validated_chunks = []
    i = 0

    while i < len(final_chunks):
        current_chunk = final_chunks[i]
        current_size = get_word_count(current_chunk)

        if current_size < min_words:
            # Try to merge with subsequent chunks
            merged_text = current_chunk["text"]
            merged_position = current_chunk["position"]
            j = i + 1

            # Keep merging until we reach min_words or run out of chunks
            while j < len(final_chunks):
                next_chunk = final_chunks[j]
                potential_merged = merged_text + " " + next_chunk["text"]
                potential_size = len(potential_merged.split())

                if potential_size <= max_words:
                    merged_text = potential_merged
                    j += 1
                    if potential_size >= min_words:
                        break
                else:
                    break

            # Add the merged result
            validated_chunks.append({"position": merged_position, "text": merged_text})

            # Skip the chunks we merged
            i = j
        else:
            # Chunk is already the right size
            validated_chunks.append(current_chunk)
            i += 1  # Final validation: ensure most chunks are within bounds
    # Allow up to 1 chunk to be outside the bounds for practical reasons
    final_result = []

    for chunk in validated_chunks:
        size = get_word_count(chunk)

        if size > max_words:
            # Split oversized chunks - these should always be fixed
            final_result.extend(split_large_chunk(chunk, max_words))
        else:
            final_result.append(chunk)

    # Count how many chunks are below minimum and try to fix them if reasonable
    small_chunks = [
        i for i, chunk in enumerate(final_result) if get_word_count(chunk) < min_words
    ]

    if len(small_chunks) > 1:
        # Try to merge some small chunks
        i = 0
        while i < len(final_result) - 1:
            current_size = get_word_count(final_result[i])
            next_size = get_word_count(final_result[i + 1])

            if current_size < min_words or next_size < min_words:
                combined_size = current_size + next_size
                if combined_size <= max_words:
                    # Merge these chunks
                    final_result[i] = {
                        "position": final_result[i]["position"],
                        "text": final_result[i]["text"]
                        + " "
                        + final_result[i + 1]["text"],
                    }
                    final_result.pop(i + 1)
                    continue
            i += 1

    return final_result
