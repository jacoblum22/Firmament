import pytest
import os
import json
import sys
from unittest.mock import patch, MagicMock

# Ensure we can import from utils by adding the parent directory to path
if __name__ == "__main__" or "pytest" in sys.modules:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(os.path.dirname(current_dir))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

from utils.bertopic_processor import process_with_bertopic


@pytest.fixture
def sample_chunks():
    return [
        {"position": 0, "text": "The cat sat on the mat."},
        {"position": 1, "text": "Dogs are friendly animals."},
        {"position": 2, "text": "Cats and dogs can be great pets."},
        {"position": 3, "text": "Birds can fly high in the sky."},
    ]


@pytest.fixture
def mock_generate_cluster_headings():
    # Returns ([headings_data], total_tokens)
    return (
        [
            {"concept": "cat, mat", "heading": "Cats", "summary": "About cats."},
            {"concept": "dog, animal", "heading": "Dogs", "summary": "About dogs."},
        ],
        42,
    )


@pytest.fixture
def mock_bertopic_fit_transform():
    # topics: [0, 1, 0, -1] means 2 topics and 1 noise
    return [0, 1, 0, -1], [0.9, 0.8, 0.95, 0.1]


@pytest.fixture
def mock_bertopic_get_topic():
    # Return a list of (word, score) tuples
    return [("cat", 0.5), ("mat", 0.3), ("dog", 0.2), ("animal", 0.1), ("pet", 0.05)]


@patch(
    "utils.bertopic_processor.stopwords.words",
    return_value=["the", "on", "in", "are", "can"],
)
@patch("utils.bertopic_processor.BERTopic")
@patch("utils.bertopic_processor.generate_cluster_headings")
@patch("utils.bertopic_processor.pre_cluster_with_kmeans")
def test_process_with_bertopic_basic(
    mock_pre_cluster,
    mock_generate_headings,
    mock_bertopic_cls,
    mock_stopwords,
    sample_chunks,
    mock_generate_cluster_headings,
    mock_bertopic_fit_transform,
    mock_bertopic_get_topic,
):
    # Debug print to check chunks
    print(f"DEBUG: sample_chunks in test: {sample_chunks}")

    # Mock k-means to return single cluster (no splitting for small dataset)
    mock_pre_cluster.return_value = [sample_chunks]
    # Setup mocks
    mock_generate_headings.return_value = mock_generate_cluster_headings
    mock_topic_model = MagicMock()
    mock_topic_model.fit_transform.return_value = mock_bertopic_fit_transform
    mock_topic_model.get_topic.return_value = mock_bertopic_get_topic
    mock_bertopic_cls.return_value = mock_topic_model

    result = process_with_bertopic(sample_chunks)
    print(f"DEBUG: result in test: {result}")

    assert result["num_chunks"] == 4
    assert result["num_topics"] == 2
    assert result["total_tokens_used"] == 42
    assert "topics" in result
    assert set(result["topics"].keys()) == {"0", "1"}
    for tid, topic in result["topics"].items():
        assert "concepts" in topic
        assert "heading" in topic
        assert "summary" in topic
        assert "keywords" in topic
        assert isinstance(topic["keywords"], list)
        assert "examples" in topic
        assert isinstance(topic["examples"], list)
        assert "stats" in topic


@patch(
    "utils.bertopic_processor.stopwords.words",
    return_value=["the", "on", "in", "are", "can"],
)
@patch("utils.bertopic_processor.BERTopic")
@patch("utils.bertopic_processor.generate_cluster_headings")
@patch("utils.bertopic_processor.pre_cluster_with_kmeans")
def test_process_with_bertopic_kmeans_clustering(
    mock_pre_cluster,
    mock_generate_headings,
    mock_bertopic_cls,
    mock_stopwords,
    sample_chunks,
    mock_generate_cluster_headings,
    mock_bertopic_fit_transform,
    mock_bertopic_get_topic,
):
    """Test BERTopic processing when k-means splits data into multiple clusters."""
    # Mock k-means to return two clusters
    cluster1 = sample_chunks[:2]
    cluster2 = sample_chunks[2:]
    mock_pre_cluster.return_value = [cluster1, cluster2]

    # Mock headings for both clusters
    mock_generate_headings.return_value = (
        [
            {"concept": "cat", "heading": "Cats", "summary": "About cats."},
            {"concept": "dog", "heading": "Dogs", "summary": "About dogs."},
        ],
        30,
    )

    # Setup BERTopic mocks
    mock_topic_model = MagicMock()
    mock_topic_model.fit_transform.return_value = ([0, 0], [0.9, 0.8])
    mock_topic_model.get_topic.return_value = mock_bertopic_get_topic
    mock_bertopic_cls.return_value = mock_topic_model

    result = process_with_bertopic(sample_chunks)

    # Should still process all chunks
    assert result["num_chunks"] == 4
    # Should have topics from both clusters (with ID offsets)
    assert result["num_topics"] >= 2
    assert "topics" in result

    # Check that topic IDs include offset (cluster 1 should have IDs like 1000, 1001)
    topic_ids = list(result["topics"].keys())
    assert len(topic_ids) >= 2

    # Verify k-means was called
    mock_pre_cluster.assert_called_once_with(sample_chunks)


@patch(
    "utils.bertopic_processor.stopwords.words",
    return_value=["the", "on", "in", "are", "can"],
)
@patch("utils.bertopic_processor.generate_cluster_headings")
def test_process_with_bertopic_empty_chunks(mock_generate_headings, mock_stopwords):
    result = process_with_bertopic([])
    assert result == {
        "num_chunks": 0,
        "num_topics": 0,
        "total_tokens_used": 0,
        "topics": {},
    }


@patch(
    "utils.bertopic_processor.stopwords.words",
    return_value=["the", "on", "in", "are", "can"],
)
@patch("utils.bertopic_processor.BERTopic")
@patch("utils.bertopic_processor.generate_cluster_headings")
def test_process_with_bertopic_save_file(
    mock_generate_headings,
    mock_bertopic_cls,
    mock_stopwords,
    tmp_path,
    sample_chunks,
    mock_generate_cluster_headings,
    mock_bertopic_fit_transform,
    mock_bertopic_get_topic,
):
    # Debug print to check chunks
    print(f"DEBUG: sample_chunks in test: {sample_chunks}")
    # Setup mocks
    mock_generate_headings.return_value = mock_generate_cluster_headings
    mock_topic_model = MagicMock()
    mock_topic_model.fit_transform.return_value = mock_bertopic_fit_transform
    mock_topic_model.get_topic.return_value = mock_bertopic_get_topic
    mock_bertopic_cls.return_value = mock_topic_model

    # Patch os.makedirs and os.remove to avoid actual file system changes
    with patch("os.makedirs"), patch("os.remove"), patch(
        "os.path.exists", return_value=True
    ):
        # Patch PROCESSED_DIR to tmp_path
        with patch("utils.bertopic_processor.PROCESSED_DIR", str(tmp_path)):
            filename = "testfile.txt"
            result = process_with_bertopic(sample_chunks, filename=filename)
            # Check file exists and content
            save_path = tmp_path / "testfile_processed.json"
            assert save_path.exists()
            with open(save_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"DEBUG: loaded data from file: {data}")
            assert "segments" in data
            assert "clusters" in data
            assert "meta" in data
            assert data["num_chunks"] == 4
            assert data["num_topics"] == 2


@patch(
    "utils.bertopic_processor.stopwords.words",
    return_value=["the", "on", "in", "are", "can"],
)
@patch("utils.bertopic_processor.BERTopic")
@patch("utils.bertopic_processor.generate_cluster_headings")
def test_process_with_bertopic_fallback_parameters(
    mock_generate_headings,
    mock_bertopic_cls,
    mock_stopwords,
    sample_chunks,
    mock_generate_cluster_headings,
    mock_bertopic_fit_transform,
    mock_bertopic_get_topic,
):
    # Setup mocks
    mock_generate_headings.return_value = mock_generate_cluster_headings
    mock_topic_model = MagicMock()

    # First call to fit_transform raises ValueError, second call returns normally
    def fit_transform_side_effect(*args, **kwargs):
        if not hasattr(fit_transform_side_effect, "called"):
            fit_transform_side_effect.called = True
            raise ValueError("max_df corresponds to < documents than min_df")
        return mock_bertopic_fit_transform

    mock_topic_model.fit_transform.side_effect = fit_transform_side_effect
    mock_topic_model.get_topic.return_value = mock_bertopic_get_topic
    mock_bertopic_cls.return_value = mock_topic_model

    result = process_with_bertopic(sample_chunks)
    assert result["num_topics"] == 2
    assert "topics" in result
