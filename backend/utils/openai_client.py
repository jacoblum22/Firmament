import os
import logging
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Default singleton client (used when no per-request key is provided)
_default_client = None

# LLM provider configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()  # "openai" or "ollama"
LLM_BASE_URL = os.getenv(
    "LLM_BASE_URL", ""
)  # Custom base URL (e.g., http://localhost:11434/v1)
LLM_DEFAULT_MODEL = os.getenv(
    "LLM_DEFAULT_MODEL", ""
)  # Override model name for all calls

# Ollama defaults
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")


def _resolve_base_url() -> str | None:
    """Determine the base URL based on provider config."""
    if LLM_BASE_URL:
        return LLM_BASE_URL
    if LLM_PROVIDER == "ollama":
        return OLLAMA_BASE_URL
    return None  # Use OpenAI default


def get_openai_client(api_key: str | None = None, base_url_override: str | None = None) -> OpenAI:
    """
    Get an OpenAI-compatible client.

    Args:
        api_key: Optional API key from user request. If provided, creates a
                 fresh client with this key (not cached). If None, uses the
                 server-configured default.
        base_url_override: Optional base URL override from user request header.
                          Takes precedence over server-configured LLM_BASE_URL.

    Returns:
        OpenAI client instance

    Raises:
        EnvironmentError: If no API key is available (for OpenAI provider)
    """
    base_url = base_url_override or _resolve_base_url()

    # Per-request client with user-provided key
    if api_key:
        return OpenAI(api_key=api_key, base_url=base_url)

    # Ollama doesn't need an API key
    if LLM_PROVIDER == "ollama":
        return OpenAI(api_key="ollama", base_url=base_url)

    # Default singleton client
    global _default_client
    if _default_client is None:
        env_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not env_key:
            raise EnvironmentError(
                "No API key available. Either set OPENAI_API_KEY in the server "
                "environment, or pass your API key via the X-OpenAI-Key header."
            )
        _default_client = OpenAI(api_key=env_key, base_url=base_url)
        logger.info("Default OpenAI client initialized")

    return _default_client


def get_default_model(intended_model: str, model_override: str | None = None) -> str:
    """Return the model to use, respecting overrides.

    Priority: per-request model_override > LLM_DEFAULT_MODEL env > provider default.
    For Ollama, defaults to 'llama3.1' if no override is set.
    For OpenAI, uses the intended model from the calling code.
    """
    if model_override:
        return model_override
    if LLM_DEFAULT_MODEL:
        return LLM_DEFAULT_MODEL
    if LLM_PROVIDER == "ollama":
        return "llama3.1"
    return intended_model


def get_llm_status() -> dict:
    """Return current LLM provider configuration status."""
    env_key = os.getenv("OPENAI_API_KEY", "").strip()
    return {
        "provider": LLM_PROVIDER,
        "base_url": _resolve_base_url() or "https://api.openai.com/v1",
        "default_model": LLM_DEFAULT_MODEL
        or ("llama3.1" if LLM_PROVIDER == "ollama" else ""),
        "has_server_key": bool(env_key),
        "requires_user_key": LLM_PROVIDER == "openai" and not env_key,
    }


def reset_client():
    """Reset the client instance (useful for testing or re-initialization)."""
    global _default_client
    _default_client = None
