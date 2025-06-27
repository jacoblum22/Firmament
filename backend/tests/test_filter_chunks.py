import pytest

from utils.filter_chunks import is_informative, filter_chunks


class TestIsInformative:
    """Test cases for the is_informative function"""

    def test_informative_text_returns_true(self):
        """Test that informative text with meaningful content returns True"""
        text = "This is a meaningful sentence about machine learning algorithms and their applications."
        assert is_informative(text) == True

    def test_short_text_returns_false(self):
        """Test that very short text returns False"""
        text = "Hi there"
        assert is_informative(text, min_words=5) == False

    def test_mostly_stopwords_returns_false(self):
        """Test that text with mostly stopwords returns False"""
        text = "and the of to a in is it you that he was for on are as with"
        assert is_informative(text, max_stopword_ratio=0.75) == False

    def test_balanced_content_returns_true(self):
        """Test that text with balanced content returns True"""
        text = "The algorithm processes data using machine learning techniques and statistical methods."
        assert is_informative(text) == True

    def test_technical_content_returns_true(self):
        """Test that technical content with domain-specific terms returns True"""
        text = "Neural networks utilize backpropagation algorithms to optimize weights during training phases."
        assert is_informative(text) == True

    def test_empty_text_returns_false(self):
        """Test that empty text returns False"""
        text = ""
        assert is_informative(text) == False

    def test_whitespace_only_returns_false(self):
        """Test that whitespace-only text returns False"""
        text = "   \n\t  "
        assert is_informative(text) == False

    def test_punctuation_only_returns_false(self):
        """Test that punctuation-only text returns False"""
        text = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        assert is_informative(text) == False

    def test_custom_min_words_threshold(self):
        """Test custom minimum words threshold"""
        text = "Machine learning algorithms"
        assert is_informative(text, min_words=2) == True
        assert is_informative(text, min_words=5) == False

    def test_custom_stopword_ratio_threshold(self):
        """Test custom stopword ratio threshold"""
        text = "and the of to machine learning"
        # With stricter threshold (0.5), should return False
        assert is_informative(text, max_stopword_ratio=0.5) == False
        # With lenient threshold (0.9), should return True
        assert is_informative(text, max_stopword_ratio=0.9) == True

    def test_mixed_case_handling(self):
        """Test that mixed case text is handled correctly"""
        text = "THE Algorithm PROCESSES data Using MACHINE learning TECHNIQUES"
        assert is_informative(text) == True

    def test_numbers_and_special_chars(self):
        """Test text with numbers and special characters"""
        text = (
            "The model achieved 95% accuracy with 1000 samples and α=0.01 learning rate"
        )
        assert is_informative(text) == True


class TestFilterChunks:
    """Test cases for the filter_chunks function"""

    def test_filter_informative_chunks(self):
        """Test filtering keeps informative chunks"""
        chunks = [
            {
                "position": "0:30",
                "text": "Machine learning algorithms are used to analyze large datasets and extract patterns.",
            },
            {"position": "30:60", "text": "and the of to a in is it"},
            {
                "position": "60:90",
                "text": "Neural networks utilize backpropagation for training deep learning models effectively.",
            },
        ]

        filtered = filter_chunks(chunks)
        assert len(filtered) == 2
        assert filtered[0]["text"].startswith("Machine learning")
        assert filtered[1]["text"].startswith("Neural networks")

    def test_filter_short_chunks(self):
        """Test filtering removes short chunks"""
        chunks = [
            {"position": "0:10", "text": "Hi"},
            {
                "position": "10:40",
                "text": "This is a comprehensive explanation of the algorithm's functionality.",
            },
            {"position": "40:50", "text": "Yes"},
        ]

        filtered = filter_chunks(chunks, min_words=5)
        assert len(filtered) == 1
        assert filtered[0]["text"].startswith("This is a comprehensive")

    def test_empty_chunks_list(self):
        """Test filtering empty chunks list"""
        chunks = []
        filtered = filter_chunks(chunks)
        assert filtered == []

    def test_all_chunks_filtered_out(self):
        """Test when all chunks are filtered out"""
        chunks = [
            {"position": "0:10", "text": "Hi"},
            {"position": "10:20", "text": "Yes"},
            {"position": "20:30", "text": "and the of"},
        ]

        filtered = filter_chunks(chunks, min_words=5)
        assert filtered == []

    def test_no_chunks_filtered_out(self):
        """Test when no chunks are filtered out"""
        chunks = [
            {
                "position": "0:30",
                "text": "Machine learning algorithms process data efficiently using advanced mathematical techniques.",
            },
            {
                "position": "30:60",
                "text": "Deep learning models require extensive training datasets to achieve optimal performance levels.",
            },
        ]

        filtered = filter_chunks(chunks)
        assert len(filtered) == 2
        assert filtered == chunks

    def test_custom_parameters(self):
        """Test filter_chunks with custom parameters"""
        chunks = [
            {"position": "0:20", "text": "algorithm processes data"},
            {"position": "20:40", "text": "and the of to a"},
        ]

        # With stricter parameters
        filtered_strict = filter_chunks(chunks, min_words=5, max_stopword_ratio=0.5)
        assert len(filtered_strict) == 0

        # With lenient parameters - second chunk has 100% stopwords so still gets filtered
        filtered_lenient = filter_chunks(chunks, min_words=2, max_stopword_ratio=0.9)
        assert len(filtered_lenient) == 1  # Only "algorithm processes data" passes

    def test_chunk_structure_preserved(self):
        """Test that chunk structure is preserved after filtering"""
        chunks = [
            {
                "position": "0:30",
                "text": "Machine learning algorithms analyze datasets to discover hidden patterns and insights.",
                "additional_field": "extra_data",
            }
        ]

        filtered = filter_chunks(chunks)
        assert len(filtered) == 1
        assert filtered[0]["position"] == "0:30"
        assert "Machine learning" in filtered[0]["text"]
        assert filtered[0]["additional_field"] == "extra_data"

    def test_mixed_quality_chunks(self):
        """Test filtering with mixed quality chunks"""
        chunks = [
            {"position": "0:15", "text": "Introduction to the topic"},
            {"position": "15:25", "text": "um uh well"},
            {
                "position": "25:50",
                "text": "The fundamental principles of quantum mechanics",
            },
            {"position": "50:60", "text": "and and and"},
            {
                "position": "60:90",
                "text": "Statistical analysis reveals significant correlations between variables",
            },
        ]

        filtered = filter_chunks(chunks)
        # Should keep chunks 2 and 4 (only those with 5+ words and acceptable stopword ratios)
        assert len(filtered) == 2
        assert any("quantum mechanics" in chunk["text"] for chunk in filtered)
        assert any("Statistical analysis" in chunk["text"] for chunk in filtered)


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_malformed_chunk_structure(self):
        """Test handling of chunks without expected keys"""
        # This should raise a KeyError if the chunk doesn't have 'text' key
        chunks = [{"position": "0:10"}]  # Missing 'text' key

        with pytest.raises(KeyError):
            filter_chunks(chunks)

    def test_none_text_handling(self):
        """Test handling of None text values"""
        chunks = [{"position": "0:10", "text": None}]

        with pytest.raises(AttributeError):
            filter_chunks(chunks)

    def test_numeric_text_handling(self):
        """Test handling of numeric values as text"""
        chunks = [{"position": "0:10", "text": 12345}]

        with pytest.raises(AttributeError):
            filter_chunks(chunks)

    def test_unicode_text_handling(self):
        """Test handling of unicode text"""
        chunks = [
            {
                "position": "0:30",
                "text": "Machine learning algorithms utilize mathematical concepts like α, β, and ∑ symbols.",
            }
        ]

        filtered = filter_chunks(chunks)
        assert len(filtered) == 1
        assert "Machine learning" in filtered[0]["text"]


if __name__ == "__main__":
    pytest.main([__file__])
