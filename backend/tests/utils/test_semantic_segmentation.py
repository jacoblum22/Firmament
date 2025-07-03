import pytest
from backend.utils.semantic_segmentation import semantic_segment


def test_single_sentence_returns_whole_text():
    text = "This is a single sentence."
    result = semantic_segment(text)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["position"] == "0"
    assert result[0]["text"] == text.strip()


def test_two_similar_sentences_no_split():
    text = "The cat sat on the mat. The cat is on the mat."
    result = semantic_segment(
        text, similarity_threshold=0.1
    )  # Low threshold to avoid split
    assert len(result) == 1
    assert result[0]["text"] == text


def test_two_dissimilar_sentences_split():
    text = "The sun is bright. I love eating pizza."
    result = semantic_segment(
        text, similarity_threshold=0.8
    )  # High threshold to force split
    assert len(result) == 2
    assert result[0]["position"] == "0"
    assert result[1]["position"] == "1"
    assert "The sun is bright." in result[0]["text"]
    assert "I love eating pizza." in result[1]["text"]


def test_multiple_sentences_mixed_similarity():
    text = (
        "Dogs are friendly animals. They like to play fetch. "
        "Quantum mechanics is a branch of physics. It deals with subatomic particles."
    )
    result = semantic_segment(text, similarity_threshold=0.5)
    assert len(result) >= 2
    assert result[0]["position"] == "0"
    assert result[-1]["position"] == str(len(result) - 1)
    # Ensure all text is covered
    reconstructed = " ".join([seg["text"] for seg in result])
    assert reconstructed.replace("  ", " ").strip() == text.strip()


def test_empty_string_returns_empty_segment():
    text = ""
    result = semantic_segment(text)
    assert len(result) == 1
    assert result[0]["position"] == "0"
    assert result[0]["text"] == ""


def test_sentence_with_various_punctuation():
    text = "Hello! How are you? I'm fine."
    result = semantic_segment(text, similarity_threshold=0.1)
    assert isinstance(result, list)
    assert (
        len(result) == 1 or len(result) == 3
    )  # Depending on similarity, but should not error


@pytest.mark.parametrize(
    "threshold,expected_min_segments",
    [
        (0.1, 1),
        (0.9, 3),
    ],
)
def test_threshold_effect_on_segmentation(threshold, expected_min_segments):
    text = "Apple is a fruit. Cars are vehicles. The sky is blue."
    result = semantic_segment(text, similarity_threshold=threshold)
    assert len(result) >= expected_min_segments
