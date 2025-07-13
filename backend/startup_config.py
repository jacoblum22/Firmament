"""
Startup configuration to control heavy imports and model loading.
This helps reduce backend startup time by deferring expensive operations.
"""

import os
from functools import lru_cache
from typing import Optional

# Environment variable to control startup behavior
LAZY_LOADING = os.getenv("LAZY_LOADING", "true").lower() == "true"
PRELOAD_MODELS = os.getenv("PRELOAD_MODELS", "false").lower() == "true"


@lru_cache(maxsize=1)
def should_preload_models() -> bool:
    """Determine if models should be preloaded on startup."""
    return PRELOAD_MODELS


@lru_cache(maxsize=1)
def is_lazy_loading_enabled() -> bool:
    """Determine if lazy loading is enabled."""
    return LAZY_LOADING


def get_model_cache_dir() -> str:
    """Get the directory for caching models."""
    cache_dir = os.getenv("MODEL_CACHE_DIR", "./models")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


class ModelManager:
    """Singleton to manage model loading and caching."""

    _instance: Optional["ModelManager"] = None
    _whisper_model = None
    _bertopic_model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_whisper_model(self, model_size: str = "base.en"):
        """Lazy load Whisper model."""
        if self._whisper_model is None:
            try:
                from faster_whisper import WhisperModel

                cache_dir = get_model_cache_dir()
                model_path = os.path.join(cache_dir, f"faster-whisper-{model_size}")

                if not os.path.exists(model_path):
                    print(f"Downloading Whisper model: {model_size}")

                self._whisper_model = WhisperModel(
                    model_size, download_root=cache_dir, device="auto"
                )
                print(f"Whisper model {model_size} loaded successfully")
            except Exception as e:
                print(f"Failed to load Whisper model: {e}")
                raise
        return self._whisper_model

    def get_bertopic_model(self):
        """Lazy load BERTopic model."""
        if self._bertopic_model is None:
            try:
                from bertopic import BERTopic
                from sklearn.feature_extraction.text import CountVectorizer

                # Use lighter configuration for faster startup
                vectorizer = CountVectorizer(
                    max_features=1000,  # Limit features for faster processing
                    stop_words="english",
                    ngram_range=(1, 2),
                )

                self._bertopic_model = BERTopic(
                    vectorizer_model=vectorizer,
                    verbose=False,  # Reduce output
                    calculate_probabilities=False,  # Faster processing
                )
                print("BERTopic model initialized successfully")
            except Exception as e:
                print(f"Failed to initialize BERTopic model: {e}")
                raise
        return self._bertopic_model

    def warmup_models(self):
        """Preload models if configured to do so."""
        if should_preload_models():
            print("Warming up models...")
            try:
                self.get_whisper_model()
                self.get_bertopic_model()
                print("Model warmup completed")
            except Exception as e:
                print(f"Model warmup failed: {e}")


# Global model manager instance
model_manager = ModelManager()


def configure_torch_for_startup():
    """Configure PyTorch for faster startup."""
    try:
        import torch

        # Disable CUDA initialization warnings
        os.environ.setdefault("CUDA_LAUNCH_BLOCKING", "0")

        # Set number of threads to prevent excessive CPU usage
        if torch.get_num_threads() > 4:
            torch.set_num_threads(4)

        # Disable autograd if not needed for inference
        torch.set_grad_enabled(False)

        print(
            f"PyTorch configured: {torch.get_num_threads()} threads, CUDA available: {torch.cuda.is_available()}"
        )
    except ImportError:
        pass  # PyTorch not available


def optimize_nltk_startup():
    """Optimize NLTK for faster startup."""
    try:
        import nltk
        import ssl

        # Set NLTK data path to avoid searching multiple locations
        nltk_data_dir = os.path.join(os.path.expanduser("~"), "nltk_data")
        if os.path.exists(nltk_data_dir):
            nltk.data.path = [nltk_data_dir]

        # Disable SSL certificate verification for NLTK downloads if needed
        try:
            _create_unverified_https_context = ssl._create_unverified_context
        except AttributeError:
            pass
        else:
            ssl._create_default_https_context = _create_unverified_https_context

    except ImportError:
        pass  # NLTK not available


def apply_startup_optimizations():
    """Apply all startup optimizations."""
    if is_lazy_loading_enabled():
        configure_torch_for_startup()
        optimize_nltk_startup()

        # Only warm up models if explicitly requested
        if should_preload_models():
            model_manager.warmup_models()

        print("Startup optimizations applied")
