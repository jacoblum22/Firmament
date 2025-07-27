"""Test thread safety of ModelManager."""

import threading
import time
from unittest.mock import patch
import pytest

from startup_config import ModelManager


class TestModelManagerThreadSafety:
    """Test thread safety of model loading methods."""

    def test_concurrent_whisper_model_access(self):
        """Test that concurrent access to get_whisper_model is thread-safe."""
        manager = ModelManager()
        # Reset the model to None for testing
        manager._whisper_model = None

        results = []
        errors = []

        def load_whisper_model():
            try:
                # Mock the WhisperModel import inside the method
                with patch("faster_whisper.WhisperModel") as mock_whisper:
                    mock_instance = mock_whisper.return_value
                    with patch(
                        "startup_config.get_optimal_device_config",
                        return_value=("cpu", "int8"),
                    ):
                        with patch(
                            "startup_config.get_model_cache_dir",
                            return_value="./test_models",
                        ):
                            with patch(
                                "startup_config.os.path.exists", return_value=True
                            ):
                                model = manager.get_whisper_model()
                                results.append(model)
            except Exception as e:
                errors.append(e)

        # Create multiple threads that try to load the model concurrently
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=load_whisper_model)
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check that no errors occurred
        assert len(errors) == 0, f"Errors occurred: {errors}"

        # Check that all threads got the same model instance (singleton behavior)
        assert len(results) == 10
        first_model = results[0]
        for model in results:
            assert (
                model is first_model
            ), "All threads should get the same model instance"

    def test_concurrent_bertopic_model_access(self):
        """Test that concurrent access to get_bertopic_model is thread-safe."""
        manager = ModelManager()
        # Reset the model to None for testing
        manager._bertopic_model = None

        results = []
        errors = []

        def load_bertopic_model():
            try:
                # Mock the BERTopic imports inside the method
                with patch("bertopic.BERTopic") as mock_bertopic:
                    mock_instance = mock_bertopic.return_value
                    with patch("sklearn.feature_extraction.text.CountVectorizer"):
                        model = manager.get_bertopic_model()
                        results.append(model)
            except Exception as e:
                errors.append(e)

        # Create multiple threads that try to load the model concurrently
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=load_bertopic_model)
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check that no errors occurred
        assert len(errors) == 0, f"Errors occurred: {errors}"

        # Check that all threads got the same model instance (singleton behavior)
        assert len(results) == 10
        first_model = results[0]
        for model in results:
            assert (
                model is first_model
            ), "All threads should get the same model instance"

    def test_mixed_concurrent_model_access(self):
        """Test concurrent access to both model types simultaneously."""
        manager = ModelManager()
        # Reset both models to None for testing
        manager._whisper_model = None
        manager._bertopic_model = None

        whisper_results = []
        bertopic_results = []
        errors = []

        def load_whisper_model():
            try:
                with patch("faster_whisper.WhisperModel") as mock_whisper:
                    mock_instance = mock_whisper.return_value
                    with patch(
                        "startup_config.get_optimal_device_config",
                        return_value=("cpu", "int8"),
                    ):
                        with patch(
                            "startup_config.get_model_cache_dir",
                            return_value="./test_models",
                        ):
                            with patch(
                                "startup_config.os.path.exists", return_value=True
                            ):
                                model = manager.get_whisper_model()
                                whisper_results.append(model)
            except Exception as e:
                errors.append(e)

        def load_bertopic_model():
            try:
                with patch("bertopic.BERTopic") as mock_bertopic:
                    mock_instance = mock_bertopic.return_value
                    with patch("sklearn.feature_extraction.text.CountVectorizer"):
                        model = manager.get_bertopic_model()
                        bertopic_results.append(model)
            except Exception as e:
                errors.append(e)

        # Create threads for both model types
        threads = []
        for _ in range(5):
            whisper_thread = threading.Thread(target=load_whisper_model)
            bertopic_thread = threading.Thread(target=load_bertopic_model)
            threads.extend([whisper_thread, bertopic_thread])

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check that no errors occurred
        assert len(errors) == 0, f"Errors occurred: {errors}"

        # Check that each model type has consistent instances
        assert len(whisper_results) == 5
        assert len(bertopic_results) == 5

        if whisper_results:
            first_whisper = whisper_results[0]
            for model in whisper_results:
                assert (
                    model is first_whisper
                ), "All Whisper models should be the same instance"

        if bertopic_results:
            first_bertopic = bertopic_results[0]
            for model in bertopic_results:
                assert (
                    model is first_bertopic
                ), "All BERTopic models should be the same instance"
