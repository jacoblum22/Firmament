import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from backend.utils.bertopic_processor import (
    get_stopwords,
    redistribute_large_topics,
    NLTK_AVAILABLE,
)


class TestGetStopwords:
    """Test the NLTK stopwords fallback system."""

    @patch("backend.utils.bertopic_processor.NLTK_AVAILABLE", True)
    @patch("backend.utils.bertopic_processor.stopwords")
    def test_get_stopwords_nltk_available_success(self, mock_stopwords):
        """Test get_stopwords when NLTK is available and works."""
        mock_stopwords.words.return_value = ["the", "and", "or", "but"]

        result = get_stopwords()

        assert result == ["the", "and", "or", "but"]
        mock_stopwords.words.assert_called_once_with("english")

    @patch("backend.utils.bertopic_processor.NLTK_AVAILABLE", True)
    @patch("backend.utils.bertopic_processor.stopwords")
    def test_get_stopwords_nltk_available_lookup_error(self, mock_stopwords):
        """Test get_stopwords when NLTK is available but stopwords corpus is missing."""
        mock_stopwords.words.side_effect = LookupError("Resource not found")

        result = get_stopwords()

        assert result == "english"
        mock_stopwords.words.assert_called_once_with("english")

    @patch("backend.utils.bertopic_processor.NLTK_AVAILABLE", False)
    def test_get_stopwords_nltk_unavailable(self):
        """Test get_stopwords when NLTK is not available."""
        result = get_stopwords()

        assert result == "english"


class TestRedistributeLargeTopics:
    """Test the topic redistribution functionality."""

    @pytest.fixture
    def sample_topic_map(self):
        """Create a sample topic map with one large topic."""
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

    @pytest.fixture
    def mock_topic_model(self):
        """Create a mock BERTopic model."""
        model = MagicMock()
        return model

    def test_redistribute_large_topics_no_redistribution_needed(
        self, sample_topic_map, mock_topic_model
    ):
        """Test when no topics exceed the threshold."""
        result = redistribute_large_topics(
            sample_topic_map,
            mock_topic_model,
            cluster_id=0,
            max_topic_percentage=0.8,  # 80% threshold = 6.4 chunks max
        )

        # Should return original map unchanged
        assert result == sample_topic_map

    def test_redistribute_large_topics_insufficient_topics(self, mock_topic_model):
        """Test when there's only one topic (can't redistribute)."""
        single_topic_map = {
            "topic_0": [
                {"text": "Only one topic here", "position": 0},
                {"text": "Cannot redistribute", "position": 1},
            ]
        }

        result = redistribute_large_topics(
            single_topic_map, mock_topic_model, cluster_id=0
        )

        assert result == single_topic_map

    def test_redistribute_large_topics_normal_operation(
        self, sample_topic_map, mock_topic_model
    ):
        """Test normal redistribution operation."""
        result = redistribute_large_topics(
            sample_topic_map, mock_topic_model, cluster_id=0
        )

        # Should complete the redistribution process normally
        # topic_0 should be reduced from 6 to 4 chunks (within 60% limit)
        # topic_1 should increase from 2 to 4 chunks
        assert len(result["topic_0"]) == 4  # Reduced from 6
        assert len(result["topic_1"]) == 4  # Increased from 2


class TestIntegrationWithNewFeatures:
    """Integration tests for new features working together."""

    @patch("backend.utils.bertopic_processor.get_stopwords")
    @patch("backend.utils.bertopic_processor.BERTopic")
    @patch("backend.utils.bertopic_processor.redistribute_large_topics")
    def test_stopwords_and_redistribution_integration(
        self, mock_redistribute, mock_bertopic_cls, mock_get_stopwords
    ):
        """Test that get_stopwords and redistribution work together."""
        from backend.utils.bertopic_processor import process_cluster_with_bertopic

        # Setup mocks
        mock_get_stopwords.return_value = ["the", "and", "or"]
        mock_topic_model = MagicMock()
        mock_topic_model.fit_transform.return_value = ([0, 1, 0], [0.9, 0.8, 0.9])
        mock_bertopic_cls.return_value = mock_topic_model
        mock_redistribute.return_value = {"topic_0": [], "topic_1": []}

        chunks = [
            {"text": "First chunk", "position": 0},
            {"text": "Second chunk", "position": 1},
            {"text": "Third chunk", "position": 2},
        ]

        result = process_cluster_with_bertopic(chunks, cluster_id=0)

        # Verify get_stopwords was called
        mock_get_stopwords.assert_called()

        # Verify redistribution was called
        mock_redistribute.assert_called_once()

        # Verify result structure
        topic_map, noise_chunks, topic_model = result
        assert isinstance(topic_map, dict)
        assert isinstance(noise_chunks, list)
        assert topic_model == mock_topic_model


class TestEdgeCases:
    """Test edge cases for new functionality."""

    def test_redistribute_with_empty_topic_map(self, mock_topic_model):
        """Test redistribution with empty topic map."""
        result = redistribute_large_topics({}, mock_topic_model, 0)
        assert result == {}

    def test_redistribute_with_all_small_topics(self, mock_topic_model):
        """Test redistribution when all topics are below threshold."""
        small_topic_map = {
            "topic_0": [{"text": "Small topic 1", "position": 0}],
            "topic_1": [{"text": "Small topic 2", "position": 1}],
        }

        result = redistribute_large_topics(
            small_topic_map,
            mock_topic_model,
            cluster_id=0,
            max_topic_percentage=0.8,  # High threshold
        )

        assert result == small_topic_map


@pytest.fixture
def mock_topic_model():
    """Fixture for creating mock BERTopic model."""
    return MagicMock()
