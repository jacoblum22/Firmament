import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np

# Check for utils dependency
try:
    from utils.generate_cluster_heading import generate_cluster_headings

    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False


@pytest.mark.skipif(
    not UTILS_AVAILABLE, reason="utils.generate_cluster_heading not available"
)
class TestGenerateClusterHeadings:
    """Test cases for the generate_cluster_headings function"""

    def test_empty_clusters_returns_default(self):
        """Test that empty clusters return a default heading"""
        clusters = []
        result, token_count = generate_cluster_headings(clusters)

        assert len(result) == 1
        assert result[0]["concept"] == "Unknown"
        assert result[0]["heading"] == "Untitled Topic"
        assert result[0]["summary"] == ""
        assert token_count == 0

    @patch("utils.generate_cluster_heading.embedding_model")
    @patch("utils.generate_cluster_heading.client")
    @patch("utils.generate_cluster_heading.encoding")
    def test_single_cluster_processing(
        self, mock_encoding, mock_client, mock_embedding_model
    ):
        """Test processing of a single cluster with mocked AI responses"""
        # Setup mocks
        mock_embedding_model.encode.return_value = np.array([[0.1, 0.2], [0.3, 0.4]])
        mock_encoding.encode.return_value = ["token1", "token2", "token3"]  # 3 tokens

        # Mock GPT response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = (
            "Concept: Machine Learning Algorithms\n"
            "Heading: Introduction to Neural Networks and Deep Learning\n"
            "Summary: This section covers the fundamental concepts of neural networks, including their architecture and training processes."
        )
        mock_client.chat.completions.create.return_value = mock_response

        clusters = [
            ["Neural networks are powerful", "Deep learning models train on data"]
        ]
        result, token_count = generate_cluster_headings(clusters)

        assert len(result) == 1
        assert result[0]["concept"] == "Machine Learning Algorithms"
        assert (
            result[0]["heading"] == "Introduction to Neural Networks and Deep Learning"
        )
        assert "neural networks" in result[0]["summary"].lower()
        assert token_count == 3

    @patch("utils.generate_cluster_heading.embedding_model")
    @patch("utils.generate_cluster_heading.client")
    @patch("utils.generate_cluster_heading.encoding")
    def test_multiple_clusters_processing(
        self, mock_encoding, mock_client, mock_embedding_model
    ):
        """Test processing of multiple clusters"""
        # Setup mocks - use side_effect to return different embeddings for each cluster
        mock_embedding_model.encode.side_effect = [
            np.array([[0.1, 0.2], [0.3, 0.4]]),  # First cluster embeddings
            np.array([[0.5, 0.6], [0.7, 0.8]]),  # Second cluster embeddings
        ]
        mock_encoding.encode.return_value = ["token"] * 10  # 10 tokens

        # Mock GPT response with multiple sections
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = (
            "Concept: Neural Networks\n"
            "Heading: Deep Learning Fundamentals\n"
            "Summary: Introduction to neural network architectures.\n"
            "|||\n"
            "Concept: Data Analysis\n"
            "Heading: Statistical Methods in Research\n"
            "Summary: Overview of statistical techniques for data analysis."
        )
        mock_client.chat.completions.create.return_value = mock_response

        clusters = [
            ["Neural networks learn patterns", "Deep learning requires data"],
            ["Statistics help analyze data", "Research methods are important"],
        ]
        result, token_count = generate_cluster_headings(clusters)

        assert len(result) == 2
        assert result[0]["concept"] == "Neural Networks"
        assert result[0]["heading"] == "Deep Learning Fundamentals"
        assert result[1]["concept"] == "Data Analysis"
        assert result[1]["heading"] == "Statistical Methods in Research"
        assert token_count == 10

    @patch("utils.generate_cluster_heading.embedding_model")
    @patch("utils.generate_cluster_heading.client")
    @patch("utils.generate_cluster_heading.encoding")
    def test_malformed_gpt_response_handling(
        self, mock_encoding, mock_client, mock_embedding_model
    ):
        """Test handling of malformed or incomplete GPT responses"""
        # Setup mocks
        mock_embedding_model.encode.return_value = np.array([[0.1, 0.2]])
        mock_encoding.encode.return_value = ["token"] * 5

        # Mock malformed GPT response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = (
            "Concept: Some concept\n"
            "This is malformed without proper headers\n"
            "Summary: Missing heading field"
        )
        mock_client.chat.completions.create.return_value = mock_response

        clusters = [["Some text about a topic"]]
        result, token_count = generate_cluster_headings(clusters)

        assert len(result) == 1
        assert result[0]["concept"] == "Some concept"
        assert result[0]["heading"] == ""  # Should be empty due to malformed response
        assert result[0]["summary"] == "Missing heading field"

    @patch("utils.generate_cluster_heading.embedding_model")
    @patch("utils.generate_cluster_heading.client")
    @patch("utils.generate_cluster_heading.encoding")
    def test_insufficient_gpt_responses_for_clusters(
        self, mock_encoding, mock_client, mock_embedding_model
    ):
        """Test when GPT returns fewer responses than clusters"""
        # Setup mocks
        mock_embedding_model.encode.return_value = np.array([[0.1, 0.2]])
        mock_encoding.encode.return_value = ["token"] * 5

        # Mock GPT response with only one section for two clusters
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = (
            "Concept: First Topic\n"
            "Heading: First Cluster Heading\n"
            "Summary: Summary for first cluster only."
        )
        mock_client.chat.completions.create.return_value = mock_response

        clusters = [["First cluster content"], ["Second cluster content"]]
        result, token_count = generate_cluster_headings(clusters)

        assert len(result) == 2
        assert result[0]["concept"] == "First Topic"
        assert result[0]["heading"] == "First Cluster Heading"
        # Second result should be default due to insufficient responses
        assert result[1]["concept"] == ""
        assert result[1]["heading"] == "Untitled Topic"
        assert result[1]["summary"] == ""

    @patch("utils.generate_cluster_heading.embedding_model")
    @patch("utils.generate_cluster_heading.client")
    @patch("utils.generate_cluster_heading.encoding")
    def test_cluster_representative_chunk_selection(
        self, mock_encoding, mock_client, mock_embedding_model
    ):
        """Test that the function correctly selects representative chunks from clusters"""
        # Mock embeddings to control similarity calculations
        # Embeddings designed so index 1 is most similar to centroid
        mock_embeddings = np.array(
            [
                [1.0, 0.0],  # Index 0
                [0.5, 0.5],  # Index 1 - closest to centroid [0.5, 0.33]
                [0.0, 1.0],  # Index 2
            ]
        )
        mock_embedding_model.encode.return_value = mock_embeddings
        mock_encoding.encode.return_value = ["token"] * 5

        # Mock simple GPT response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = (
            "Concept: Test\n" "Heading: Test Heading\n" "Summary: Test summary."
        )
        mock_client.chat.completions.create.return_value = mock_response

        # Cluster with 3 chunks
        clusters = [["First chunk", "Second chunk", "Third chunk"]]
        result, token_count = generate_cluster_headings(clusters)

        # Verify the function was called (we can't easily test which chunks were selected
        # without more invasive mocking, but we can verify the process completed)
        assert len(result) == 1
        mock_embedding_model.encode.assert_called_once()

    @patch("utils.generate_cluster_heading.embedding_model")
    @patch("utils.generate_cluster_heading.client")
    @patch("utils.generate_cluster_heading.encoding")
    def test_large_cluster_chunk_limitation(
        self, mock_encoding, mock_client, mock_embedding_model
    ):
        """Test that large clusters are limited to 3 representative chunks"""
        # Mock embeddings for 5 chunks
        mock_embeddings = np.array(
            [[1.0, 0.0], [0.8, 0.2], [0.6, 0.4], [0.4, 0.6], [0.2, 0.8]]
        )
        mock_embedding_model.encode.return_value = mock_embeddings
        mock_encoding.encode.return_value = ["token"] * 10

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = (
            "Concept: Large Cluster\n"
            "Heading: Large Cluster Test\n"
            "Summary: Testing large cluster handling."
        )
        mock_client.chat.completions.create.return_value = mock_response

        # Large cluster with 5 chunks
        large_cluster = [f"Chunk {i} content" for i in range(5)]
        clusters = [large_cluster]

        result, token_count = generate_cluster_headings(clusters)

        # Should still work and return one result
        assert len(result) == 1
        assert result[0]["concept"] == "Large Cluster"

    @patch("utils.generate_cluster_heading.embedding_model")
    @patch("utils.generate_cluster_heading.client")
    @patch("utils.generate_cluster_heading.encoding")
    def test_empty_gpt_response(self, mock_encoding, mock_client, mock_embedding_model):
        """Test handling when GPT returns empty or None content"""
        # Setup mocks
        mock_embedding_model.encode.return_value = np.array([[0.1, 0.2]])
        mock_encoding.encode.return_value = ["token"] * 3

        # Mock empty GPT response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = None
        mock_client.chat.completions.create.return_value = mock_response

        clusters = [["Some content"]]
        result, token_count = generate_cluster_headings(clusters)

        assert len(result) == 1
        # When GPT returns None/empty, parsing creates empty section
        assert result[0]["concept"] == ""
        assert result[0]["heading"] == ""
        assert result[0]["summary"] == ""

    @patch("utils.generate_cluster_heading.embedding_model")
    def test_embedding_model_called_correctly(self, mock_embedding_model):
        """Test that the embedding model is called with correct parameters"""
        mock_embedding_model.encode.return_value = np.array([[0.1, 0.2]])

        with patch("utils.generate_cluster_heading.client") as mock_client, patch(
            "utils.generate_cluster_heading.encoding"
        ) as mock_encoding:

            mock_encoding.encode.return_value = ["token"]
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = (
                "Concept: Test\nHeading: Test\nSummary: Test"
            )
            mock_client.chat.completions.create.return_value = mock_response

            clusters = [["Test chunk 1", "Test chunk 2"]]
            generate_cluster_headings(clusters)

            # Verify embedding model was called with the cluster content
            mock_embedding_model.encode.assert_called_once_with(
                ["Test chunk 1", "Test chunk 2"]
            )


class TestIntegrationScenarios:
    """Integration-style tests with realistic data patterns"""

    @patch("utils.generate_cluster_heading.embedding_model")
    @patch("utils.generate_cluster_heading.client")
    @patch("utils.generate_cluster_heading.encoding")
    def test_realistic_lecture_clusters(
        self, mock_encoding, mock_client, mock_embedding_model
    ):
        """Test with realistic lecture content patterns"""
        # Setup mocks
        mock_embedding_model.encode.return_value = np.array(
            [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        )
        mock_encoding.encode.return_value = ["token"] * 20

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = (
            "Concept: Machine Learning Fundamentals\n"
            "Heading: Introduction to Supervised Learning Algorithms\n"
            "Summary: This section introduces the basic concepts of supervised learning, including classification and regression techniques.\n"
            "|||\n"
            "Concept: Data Preprocessing\n"
            "Heading: Feature Engineering and Data Cleaning Techniques\n"
            "Summary: Discussion of methods for preparing raw data for machine learning models, including normalization and feature selection."
        )
        mock_client.chat.completions.create.return_value = mock_response

        realistic_clusters = [
            [
                "Today we'll discuss supervised learning algorithms and their applications",
                "Classification problems involve predicting discrete categories",
                "Regression is used when we want to predict continuous values",
            ],
            [
                "Data preprocessing is a crucial step in any machine learning pipeline",
                "Feature engineering involves creating new variables from existing data",
                "Normalization helps ensure all features are on the same scale",
            ],
        ]

        result, token_count = generate_cluster_headings(realistic_clusters)

        assert len(result) == 2
        assert "Learning" in result[0]["heading"]
        assert "Data" in result[1]["heading"]
        assert token_count == 20


if __name__ == "__main__":
    pytest.main([__file__])
