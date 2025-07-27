#!/usr/bin/env python3
"""
Test script for the new k-means pre-clustering functionality in BERTopic processor.
"""

import os
from unittest.mock import patch, MagicMock

try:
    from utils.bertopic_processor import process_with_bertopic

    BERTOPIC_AVAILABLE = True
except ImportError:
    BERTOPIC_AVAILABLE = False
    print("⚠️  Warning: BERTopic module not available. K-means tests will be skipped.")


def test_kmeans_clustering():
    """Test k-means pre-clustering functionality with BERTopic processor"""
    if not BERTOPIC_AVAILABLE:
        print("⚠️  Skipping k-means test - BERTopic module not available")
        return

    # Mock the OpenAI client to avoid real API calls during testing
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[
        0
    ].message.content = """Concept: neural networks, deep learning, computational models
Heading: Neural Networks and Deep Learning Fundamentals
Summary: This section covers the basics of neural networks as computational models inspired by biological systems, and introduces deep learning with its multiple layers and backpropagation training method.
|||
Concept: machine learning, algorithms, data science
Heading: Machine Learning Algorithms and Applications
Summary: This section discusses various machine learning algorithms, their applications in data science, and how they are used to solve complex problems in artificial intelligence.
|||
Concept: computer vision, natural language processing, applications
Heading: AI Applications in Vision and Language Processing
Summary: This section explores practical applications of AI including computer vision techniques for image processing and natural language processing methods for text analysis."""

    with patch(
        "utils.generate_cluster_heading.client.chat.completions.create",
        return_value=mock_response,
    ):
        # Create test chunks that should be separable by k-means
        test_chunks = [
            {
                "position": "0",
                "text": "Neural networks are computational models inspired by biological systems. They process information through interconnected nodes.",
            },
            {
                "position": "1",
                "text": "Deep learning uses multiple layers of neural networks to learn complex patterns. Backpropagation is used for training.",
            },
            {
                "position": "2",
                "text": "Convolutional neural networks excel at image recognition tasks. They use filters to detect visual features.",
            },
            {
                "position": "3",
                "text": "Artificial intelligence encompasses many different techniques for creating intelligent systems and automated reasoning.",
            },
            {
                "position": "4",
                "text": "Machine learning enables systems to learn from data without explicit programming. It's a core AI component.",
            },
            {
                "position": "5",
                "text": "Reinforcement learning involves agents learning through environmental interaction and reward mechanisms.",
            },
            {
                "position": "6",
                "text": "The training process involves gradient descent optimization to minimize loss functions in neural networks.",
            },
            {
                "position": "7",
                "text": "Computer vision systems interpret visual information using deep learning architectures like CNNs.",
            },
            {
                "position": "8",
                "text": "Natural language processing uses transformer models to understand and generate human language.",
            },
            {
                "position": "9",
                "text": "Ethics in AI considers societal implications and bias in algorithmic decision making systems.",
            },
            {
                "position": "10",
                "text": "Recurrent neural networks process sequential data and maintain internal state for temporal modeling.",
            },
            {
                "position": "11",
                "text": "Unsupervised learning discovers patterns in unlabeled data through clustering and dimensionality reduction techniques.",
            },
            {
                "position": "12",
                "text": "Feature engineering involves selecting and transforming relevant input variables for machine learning models.",
            },
            {
                "position": "13",
                "text": "Model evaluation uses cross-validation and metrics like accuracy to assess generalization performance.",
            },
            {
                "position": "14",
                "text": "Ensemble methods combine multiple models to improve prediction accuracy and robustness.",
            },
            {
                "position": "15",
                "text": "The architecture of neural networks includes input layers, hidden layers, and output layers with activation functions.",
            },
            {
                "position": "16",
                "text": "Data preprocessing cleans and prepares datasets for training machine learning algorithms effectively.",
            },
            {
                "position": "17",
                "text": "Overfitting occurs when models memorize training data and fail to generalize to new examples.",
            },
            {
                "position": "18",
                "text": "Attention mechanisms in transformers capture relationships between different parts of input sequences.",
            },
            {
                "position": "19",
                "text": "The future of AI includes general artificial intelligence and human-AI collaborative systems.",
            },
        ]

        print("Testing k-means pre-clustering with BERTopic...")
        print(f"Number of test chunks: {len(test_chunks)}")

        # Process with our new k-means approach
        result = process_with_bertopic(test_chunks, filename=None)

        print(f"\n=== FINAL RESULTS ===")
        print(f"Total topics generated: {result['num_topics']}")
        print(f"Total tokens used: {result['total_tokens_used']}")

        for topic_id, topic_info in result["topics"].items():
            print(f"\nTopic {topic_id}: {topic_info['heading']}")
            print(f"  Concepts: {topic_info['concepts']}")
            print(f"  Stats: {topic_info['stats']}")
            print(f"  Summary: {topic_info['summary']}")

        # Basic assertions to make it a proper test
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "num_topics" in result, "Result should contain num_topics"
        assert "total_tokens_used" in result, "Result should contain total_tokens_used"
        assert "topics" in result, "Result should contain topics"
        assert result["num_topics"] > 0, "Should generate at least one topic"

        print("✅ K-means clustering test completed successfully!")


if __name__ == "__main__":
    test_kmeans_clustering()
