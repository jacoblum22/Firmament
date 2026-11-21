"""
Tests for the BERTopic processor pipeline.

The processor now lives at utils.nlp.bertopic_processor and has been split
into sub-modules (topic_analysis, topic_formatting, clustering, ...).

Key behaviour change: fewer than 20 chunks skip BERTopic entirely and are
treated as a single topic, so mocking BERTopic is only relevant for large
datasets (≥ 20 chunks).
"""

import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Availability guard
# ---------------------------------------------------------------------------
try:
    from utils.nlp.bertopic_processor import process_with_bertopic

    BERTOPIC_AVAILABLE = True
except ImportError:
    BERTOPIC_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not BERTOPIC_AVAILABLE, reason="utils.nlp.bertopic_processor not available"
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_chunks():
    return [
        {"position": 0, "text": "The cat sat on the mat."},
        {"position": 1, "text": "Dogs are friendly animals."},
        {"position": 2, "text": "Cats and dogs can be great pets."},
        {"position": 3, "text": "Birds can fly high in the sky."},
    ]


@pytest.fixture
def mock_headings_response():
    """Return value expected by _generate_topic_headings."""
    return (
        [{"concept": "pets, animals", "heading": "Pets and Animals", "summary": "About animals."}],
        42,
    )


def _make_large_chunks(n=25):
    """Create n artificial chunks for testing the BERTopic code path (≥ 20)."""
    topics = [
        "Machine learning is a branch of artificial intelligence.",
        "Neural networks are inspired by the human brain.",
        "Deep learning uses many layers of neural networks.",
        "Natural language processing handles text understanding.",
        "Computer vision interprets images with algorithms.",
    ]
    return [{"position": i, "text": topics[i % len(topics)]} for i in range(n)]


# ---------------------------------------------------------------------------
# Small-dataset path (< 20 chunks → skips BERTopic entirely)
# ---------------------------------------------------------------------------


@patch("utils.nlp.topic_formatting.generate_cluster_headings")
def test_process_with_bertopic_small_dataset(mock_gen, sample_chunks, mock_headings_response):
    """With < 20 chunks the processor skips BERTopic and returns one topic."""
    mock_gen.return_value = mock_headings_response

    result = process_with_bertopic(sample_chunks)

    assert result["num_chunks"] == 4
    assert result["num_topics"] == 1
    assert result["total_tokens_used"] == 42
    assert "topics" in result
    topic = next(iter(result["topics"].values()))
    assert "heading" in topic
    assert "concepts" in topic
    assert "summary" in topic
    assert "examples" in topic
    assert isinstance(topic["examples"], list)
    assert "stats" in topic


def test_process_with_bertopic_empty_chunks():
    """Empty input returns a zero-topic sentinel immediately."""
    result = process_with_bertopic([])
    assert result == {
        "num_chunks": 0,
        "num_topics": 0,
        "total_tokens_used": 0,
        "topics": {},
    }


# ---------------------------------------------------------------------------
# Large-dataset path (≥ 20 chunks → BERTopic path)
# ---------------------------------------------------------------------------


@patch("utils.nlp.topic_formatting.generate_cluster_headings")
@patch("utils.nlp.bertopic_processor.pre_cluster_with_kmeans")
def test_process_with_bertopic_large_dataset_single_cluster(
    mock_pre_cluster, mock_gen
):
    """With ≥ 20 chunks, k-means runs; single cluster → result with ≥ 1 topic."""
    large_chunks = _make_large_chunks(25)
    mock_pre_cluster.return_value = [large_chunks]
    mock_gen.return_value = (
        [{"concept": "ML", "heading": "Machine Learning", "summary": "About ML."}],
        10,
    )

    with (
        patch("utils.nlp.topic_analysis.SentenceTransformer"),
        patch("utils.nlp.topic_analysis.BERTopic") as MockBERTopic,
    ):
        mock_model = MagicMock()
        mock_model.fit_transform.return_value = ([0] * 25, [0.9] * 25)
        mock_model.get_topic.return_value = [("ml", 0.5), ("learning", 0.3)]
        MockBERTopic.return_value = mock_model

        result = process_with_bertopic(large_chunks)

    assert result["num_chunks"] == 25
    assert result["num_topics"] >= 1
    assert "topics" in result
    mock_pre_cluster.assert_called_once_with(large_chunks)


@patch("utils.nlp.topic_formatting.generate_cluster_headings")
@patch("utils.nlp.bertopic_processor.pre_cluster_with_kmeans")
def test_process_with_bertopic_large_dataset_two_clusters(
    mock_pre_cluster, mock_gen
):
    """K-means returning two clusters merges them into a combined result."""
    large_chunks = _make_large_chunks(26)
    cluster1 = large_chunks[:13]
    cluster2 = large_chunks[13:]
    mock_pre_cluster.return_value = [cluster1, cluster2]
    mock_gen.return_value = (
        [
            {"concept": "NLP", "heading": "Language Processing", "summary": "NLP."},
            {"concept": "CV", "heading": "Computer Vision", "summary": "Vision."},
        ],
        20,
    )

    with (
        patch("utils.nlp.topic_analysis.SentenceTransformer"),
        patch("utils.nlp.topic_analysis.BERTopic") as MockBERTopic,
    ):
        mock_model = MagicMock()
        mock_model.fit_transform.return_value = ([0] * 13, [0.9] * 13)
        mock_model.get_topic.return_value = [("language", 0.5)]
        MockBERTopic.return_value = mock_model

        result = process_with_bertopic(large_chunks)

    assert result["num_chunks"] == 26
    assert result["num_topics"] >= 1


# ---------------------------------------------------------------------------
# Optional features: get_stopwords / redistribute_large_topics
# ---------------------------------------------------------------------------

try:
    from utils.nlp.bertopic_processor import get_stopwords, redistribute_large_topics

    _NEW_FEATURES_AVAILABLE = BERTOPIC_AVAILABLE
except ImportError:
    _NEW_FEATURES_AVAILABLE = False


@pytest.mark.skipif(not _NEW_FEATURES_AVAILABLE, reason="optional features not present")
class TestGetStopwords:
    @patch("utils.nlp.topic_analysis.NLTK_AVAILABLE", True)
    @patch("utils.nlp.topic_analysis.stopwords")
    def test_get_stopwords_nltk_success(self, mock_sw):
        mock_sw.words.return_value = ["the", "and"]
        result = get_stopwords()
        assert "the" in result

    @patch("utils.nlp.topic_analysis.NLTK_AVAILABLE", False)
    def test_get_stopwords_nltk_unavailable(self):
        result = get_stopwords()
        assert result == "english"


@pytest.mark.skipif(not _NEW_FEATURES_AVAILABLE, reason="optional features not present")
class TestRedistributeLargeTopics:
    @pytest.fixture
    def sample_topic_map(self):
        return {
            "topic_0": [
                {"text": "Machine learning is fascinating", "position": 0},
                {"text": "Deep learning uses neural networks", "position": 1},
                {"text": "AI will change the world", "position": 2},
                {"text": "Python is great for ML", "position": 3},
                {"text": "Data science requires statistics", "position": 4},
                {"text": "Algorithms are important", "position": 5},
            ],
            "topic_1": [
                {"text": "Cats are cute animals", "position": 6},
                {"text": "Dogs are loyal pets", "position": 7},
            ],
        }

    def test_no_redistribution_needed(self, sample_topic_map):
        mock_model = MagicMock()
        result = redistribute_large_topics(
            sample_topic_map, mock_model, cluster_id=0, max_topic_percentage=0.8
        )
        assert result == sample_topic_map

    def test_insufficient_topics(self):
        mock_model = MagicMock()
        single = {"topic_0": [{"text": "only", "position": 0}]}
        result = redistribute_large_topics(single, mock_model, cluster_id=0)
        assert result == single
