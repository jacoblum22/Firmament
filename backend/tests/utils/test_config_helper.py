#!/usr/bin/env python3
"""
Test utility for handling config imports and reloading
"""

import os
import sys
import importlib
from pathlib import Path
from typing import Tuple, Any, Optional


def get_backend_dir() -> Path:
    """
    Get the backend directory path

    This works from any test file by going up the directory tree:
    - From utils/test_config_helper.py: utils -> tests -> backend
    - From config/test_*.py: config -> tests -> backend
    - From unit/test_*.py: unit -> tests -> backend
    - From integration/test_*.py: integration -> tests -> backend
    """
    current_file = Path(__file__)
    backend_dir = current_file.parents[2]  # Go up: utils -> tests -> backend
    return backend_dir


def setup_backend_path():
    """Add backend directory to Python path if not already present"""
    backend_dir = get_backend_dir()
    backend_str = str(backend_dir)
    if backend_str not in sys.path:
        sys.path.insert(0, backend_str)


def import_config() -> Tuple[Any, Any]:
    """
    Import or reimport the config module with proper cleanup

    Returns:
        Tuple[Settings, ConfigurationError]: The Settings class and ConfigurationError exception
    """
    # Ensure backend is in path
    setup_backend_path()

    # Clear any existing config module to force reload
    if "config" in sys.modules:
        del sys.modules["config"]

    # Import the config module using importlib
    config_module = importlib.import_module("config")
    return config_module.Settings, config_module.ConfigurationError


def import_config_settings() -> Any:
    """
    Import just the Settings class from config

    Returns:
        Settings: The Settings class from config module
    """
    Settings, _ = import_config()
    return Settings


def create_test_config(
    port: Optional[str] = None,
    environment: Optional[str] = None,
    openai_api_key: Optional[str] = None,
) -> Any:
    """
    Create a config Settings instance with specific test values

    Args:
        port: Port value to set (as string)
        environment: Environment to set (development/production)
        openai_api_key: OpenAI API key to set

    Returns:
        Settings: A Settings instance with the specified values
    """
    # Clear any environment variables that might interfere
    # This ensures we start with a clean slate
    env_vars_to_clear = [
        "ENVIRONMENT",
        "DEBUG",
        "HOST",
        "PORT",
        "RELOAD",
        "WORKERS",
        "ALLOWED_ORIGINS",
        "ALLOW_CREDENTIALS",
        "CORS_MAX_AGE",
        "OPENAI_API_KEY",
        "LOG_LEVEL",
    ]

    for var in env_vars_to_clear:
        if var in os.environ:
            del os.environ[var]

    # Set environment variables
    if port is not None:
        os.environ["PORT"] = port
    if environment is not None:
        os.environ["ENVIRONMENT"] = environment
    if openai_api_key is not None:
        os.environ["OPENAI_API_KEY"] = openai_api_key

    # Import fresh config
    Settings, _ = import_config()

    # Create and return settings instance
    return Settings()


def with_env_vars(**env_vars):
    """
    Decorator to temporarily set environment variables for a test

    Usage:
        @with_env_vars(PORT="8080", ENVIRONMENT="development")
        def test_something():
            # Test code here
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Store original values
            original_values = {}
            for key, value in env_vars.items():
                original_values[key] = os.environ.get(key)
                os.environ[key] = value

            try:
                # Run the test
                return func(*args, **kwargs)
            finally:
                # Restore original values
                for key, original_value in original_values.items():
                    if original_value is not None:
                        os.environ[key] = original_value
                    elif key in os.environ:
                        del os.environ[key]

        return wrapper

    return decorator


class ConfigTestContext:
    """Context manager for config testing with automatic cleanup"""

    def __init__(self, **env_vars):
        self.env_vars = env_vars
        self.original_values = {}

    def __enter__(self):
        # Store original values and set new ones BEFORE importing config
        for key, value in self.env_vars.items():
            self.original_values[key] = os.environ.get(key)
            os.environ[key] = value

        # Import fresh config with the new environment variables already set
        Settings, _ = import_config()
        settings_instance = Settings()

        return settings_instance

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original values
        for key, original_value in self.original_values.items():
            if original_value is not None:
                os.environ[key] = original_value
            elif key in os.environ:
                del os.environ[key]


# Convenience functions for common test scenarios
def create_config_with_port(port: str, environment: str = "development") -> Any:
    """Create a test config with a specific port"""
    return create_test_config(
        port=port, environment=environment, openai_api_key="sk-test1234567890abcdef"
    )


def test_config_with_custom_port() -> None:
    """Test creating a config with a custom port"""
    config = create_config_with_port(port="9000")
    assert config is not None
    assert config.port == 9000


def test_config_development() -> None:
    """Test creating a config for development environment"""
    config = create_test_config(
        environment="development", openai_api_key="sk-test1234567890abcdef"
    )
    assert config is not None
    assert config.environment == "development"
    assert config.openai_api_key == "sk-test1234567890abcdef"


def test_config_production() -> None:
    """Test creating a config for production environment"""
    config = create_test_config(
        environment="production", openai_api_key="sk-test1234567890abcdef"
    )
    assert config is not None
    assert config.environment == "production"
    assert config.openai_api_key == "sk-test1234567890abcdef"
