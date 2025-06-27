import pytest
from backend.utils.chunk_size_optimizer import optimize_chunk_sizes, get_word_count


@pytest.fixture
def simple_chunks():
    return [
        {"position": 0, "text": "This is a short chunk."},
        {"position": 1, "text": "This is another short chunk."},
        {
            "position": 2,
            "text": "This chunk is a bit longer and contains more words for testing purposes.",
        },
        {"position": 3, "text": "Short again."},
    ]


def test_get_word_count():
    chunk = {"position": 0, "text": "This is a test chunk."}
    assert get_word_count(chunk) == 5


def test_optimize_chunk_sizes_merges_small_chunks(simple_chunks):
    # Use small min_words and max_words to force merges
    optimized = optimize_chunk_sizes(
        simple_chunks, min_words=3, max_words=20, target_size=10
    )
    # Should merge some chunks
    assert all(get_word_count(chunk) >= 3 for chunk in optimized)
    assert all(get_word_count(chunk) <= 20 for chunk in optimized)
    # Should not lose any text
    original_text = " ".join(chunk["text"] for chunk in simple_chunks)
    optimized_text = " ".join(chunk["text"] for chunk in optimized)
    assert original_text.replace(" ", "") in optimized_text.replace(" ", "")


def test_optimize_chunk_sizes_handles_empty():
    assert optimize_chunk_sizes([], min_words=5, max_words=10, target_size=7) == []


def test_optimize_chunk_sizes_no_merge_needed():
    chunks = [
        {"position": 0, "text": "word " * 10},
        {"position": 1, "text": "word " * 10},
        {"position": 2, "text": "word " * 10},
    ]
    optimized = optimize_chunk_sizes(chunks, min_words=5, max_words=15, target_size=10)
    # Should not merge or split
    assert len(optimized) == 3
    for chunk in optimized:
        assert 5 <= get_word_count(chunk) <= 15


def test_optimize_chunk_sizes_split_large_chunk():
    chunk = {
        "position": 0,
        "text": "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five.",
    }
    # Set max_words low to force splitting
    optimized = optimize_chunk_sizes([chunk], min_words=2, max_words=4, target_size=3)
    # Should split into multiple chunks
    assert len(optimized) > 1
    for c in optimized:
        assert get_word_count(c) <= 4
