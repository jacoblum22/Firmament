"""
Startup configuration to control heavy imports and model loading.
This helps reduce backend startup time by deferring expensive operations.

Environment Variables:
- LAZY_LOADING: Enable/disable lazy loading (default: true)
- PRELOAD_MODELS: Preload models on startup (default: false)
- MODEL_CACHE_DIR: Directory for caching models (default: ./models)
- TORCH_NUM_THREADS: Maximum number of PyTorch threads (default: 4)
- WHISPER_DEVICE: Force specific device for Whisper model (auto-detected if not set)
- WHISPER_COMPUTE_TYPE: Force specific compute type for Whisper model (auto-selected if not set)
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


import threading


class ModelManager:
    """Singleton to manage model loading and caching."""

    _instance: Optional["ModelManager"] = None
    _lock = threading.Lock()
    _whisper_model = None
    _bertopic_model = None

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def get_whisper_model(self, model_size: str = "base.en"):
        """Lazy load Whisper model with proper device detection."""
        if self._whisper_model is None:
            try:
                from faster_whisper import WhisperModel

                device, compute_type = get_optimal_device_config()

                cache_dir = get_model_cache_dir()
                model_path = os.path.join(cache_dir, f"faster-whisper-{model_size}")

                if not os.path.exists(model_path):
                    print(f"Downloading Whisper model: {model_size}")

                self._whisper_model = WhisperModel(
                    model_size,
                    download_root=cache_dir,
                    device=device,
                    compute_type=compute_type,
                )
                print(
                    f"Whisper model {model_size} loaded successfully on {device} with {compute_type}"
                )
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
    """
    Configure PyTorch for faster startup and optimal performance.

    Sets CUDA environment variables before importing torch to ensure proper
    initialization, configures thread limits based on environment settings,
    and disables unnecessary features for inference workloads.

    Environment Variables:
        TORCH_NUM_THREADS: Maximum number of PyTorch threads (default: 4)
        CUDA_LAUNCH_BLOCKING: CUDA synchronization setting (default: 0)
    """
    try:
        # Set CUDA environment variable before importing torch to ensure it takes effect
        os.environ.setdefault("CUDA_LAUNCH_BLOCKING", "0")

        import torch

        # Get configurable thread limit from environment variable
        try:
            max_threads = int(os.getenv("TORCH_NUM_THREADS", "4"))
            if max_threads < 1:
                print(f"Warning: TORCH_NUM_THREADS must be positive, using default 4")
                max_threads = 4
        except ValueError:
            print(f"Warning: Invalid TORCH_NUM_THREADS value, using default 4")
            max_threads = 4

        # Get current thread count
        current_threads = torch.get_num_threads()

        # Set number of threads to prevent excessive CPU usage
        if current_threads > max_threads:
            torch.set_num_threads(max_threads)

        # Disable autograd if not needed for inference
        torch.set_grad_enabled(False)

        print(
            f"PyTorch configured: {torch.get_num_threads()} threads (max: {max_threads}), CUDA available: {torch.cuda.is_available()}"
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

        # Note: NLTK data should be pre-downloaded during deployment/setup phase
        # to avoid runtime downloads and maintain secure HTTPS connections.
        # Use: python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

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


def get_optimal_device_config():
    """
    Get optimal device and compute type configuration for ML models.

    Returns:
        tuple: (device, compute_type) where device is 'cuda' or 'cpu'
               and compute_type is appropriate for the device
    """
    # Valid device options
    valid_devices = ["cuda", "cpu"]
    # Valid compute types for each device
    valid_compute_types = {
        "cuda": ["float16", "float32", "int8"],
        "cpu": ["int8", "float32"],
    }

    # Check for environment variable overrides first
    env_device = os.getenv("WHISPER_DEVICE")
    env_compute_type = os.getenv("WHISPER_COMPUTE_TYPE")

    if env_device and env_compute_type:
        # Validate environment variables
        if env_device in valid_devices and env_compute_type in valid_compute_types.get(
            env_device, []
        ):
            print(
                f"Using environment-specified Whisper config: device={env_device}, compute_type={env_compute_type}"
            )
            return env_device, env_compute_type
        else:
            print(
                f"Warning: Invalid environment config device={env_device}, compute_type={env_compute_type}. Using auto-detection."
            )

    # Auto-detect optimal configuration
    try:
        import torch

        if torch.cuda.is_available():
            # Check GPU memory for optimal compute type selection
            try:
                gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (
                    1024**3
                )
                # Use float16 for GPUs with sufficient memory, int8 for lower memory
                compute_type = "float16" if gpu_memory_gb >= 6 else "int8"
                print(
                    f"Auto-detected GPU with {gpu_memory_gb:.1f}GB memory, using {compute_type}"
                )
            except Exception as e:
                print(f"Warning: Failed to get GPU memory info: {e}")
                compute_type = "float16"  # Default for CUDA
            return "cuda", compute_type
        else:
            print("CUDA not available, using CPU with int8")
            return "cpu", "int8"
    except ImportError:
        # Fallback if torch is not available
        print("PyTorch not available, using CPU with int8")
        return "cpu", "int8"
