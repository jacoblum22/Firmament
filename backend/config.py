import os
from typing import List, Optional
from dotenv import load_dotenv


class Settings:
    def __init__(self):
        # Load environment variables from .env file
        env_file = f".env.{os.getenv('ENVIRONMENT', 'development')}"
        if os.path.exists(env_file):
            load_dotenv(env_file)
        else:
            # Fallback to default .env file
            load_dotenv()

    @property
    def environment(self) -> str:
        return os.getenv("ENVIRONMENT", "development")

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def debug(self) -> bool:
        # Debug should be False in production by default
        default_debug = "false" if self.is_production else "true"
        return os.getenv("DEBUG", default_debug).lower() == "true"

    # Server Configuration
    @property
    def host(self) -> str:
        return os.getenv("HOST", "127.0.0.1" if self.is_development else "0.0.0.0")

    @property
    def port(self) -> int:
        return int(os.getenv("PORT", "8000"))

    @property
    def reload(self) -> bool:
        # Auto-reload should only be enabled in development
        return (
            os.getenv("RELOAD", "true" if self.is_development else "false").lower()
            == "true"
        )

    # CORS Configuration
    @property
    def allowed_origins(self) -> List[str]:
        origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
        # Split by comma and strip whitespace
        origins = [origin.strip() for origin in origins_str.split(",")]

        # In development, be more permissive
        if self.is_development:
            # Add common development origins if not already present
            dev_origins = [
                "http://localhost:5173",
                "http://localhost:3000",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:3000",
            ]
            for origin in dev_origins:
                if origin not in origins:
                    origins.append(origin)

        return origins

    @property
    def allow_credentials(self) -> bool:
        return os.getenv("ALLOW_CREDENTIALS", "true").lower() == "true"

    @property
    def cors_max_age(self) -> int:
        # Shorter cache in development for easier testing
        default_age = "300" if self.is_development else "3600"
        return int(os.getenv("CORS_MAX_AGE", default_age))

    # Security Configuration
    @property
    def api_key(self) -> str:
        return os.getenv("API_KEY", "")

    @property
    def secure_headers(self) -> bool:
        # Enable secure headers in production by default
        default_secure = "true" if self.is_production else "false"
        return os.getenv("SECURE_HEADERS", default_secure).lower() == "true"

    @property
    def trusted_hosts(self) -> List[str]:
        hosts_str = os.getenv("TRUSTED_HOSTS", "")
        if not hosts_str:
            return []
        return [host.strip() for host in hosts_str.split(",")]

    @property
    def rate_limit_calls(self) -> int:
        # More restrictive rate limiting in production
        default_calls = "1000" if self.is_development else "100"
        return int(os.getenv("RATE_LIMIT_CALLS", default_calls))

    @property
    def rate_limit_period(self) -> int:
        return int(os.getenv("RATE_LIMIT_PERIOD", "60"))

    # Database Configuration (for future use)
    @property
    def database_url(self) -> Optional[str]:
        return os.getenv("DATABASE_URL")

    @property
    def database_pool_size(self) -> int:
        default_pool = "5" if self.is_development else "20"
        return int(os.getenv("DATABASE_POOL_SIZE", default_pool))

    # File Storage Configuration
    @property
    def upload_max_size(self) -> int:
        # Max file size in bytes (default: 50MB for dev, 100MB for prod)
        default_size = (
            "52428800" if self.is_development else "104857600"
        )  # 50MB / 100MB
        return int(os.getenv("UPLOAD_MAX_SIZE", default_size))

    @property
    def upload_directory(self) -> str:
        return os.getenv("UPLOAD_DIRECTORY", "uploads")

    @property
    def temp_directory(self) -> str:
        return os.getenv("TEMP_DIRECTORY", "temp_chunks")

    # Logging Configuration
    @property
    def log_level(self) -> str:
        default_level = "DEBUG" if self.is_development else "INFO"
        return os.getenv("LOG_LEVEL", default_level)

    @property
    def log_file(self) -> Optional[str]:
        return os.getenv("LOG_FILE")

    # OpenAI Configuration
    @property
    def openai_api_key(self) -> str:
        return os.getenv("OPENAI_API_KEY", "")

    @property
    def openai_model(self) -> str:
        return os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    @property
    def openai_max_tokens(self) -> int:
        return int(os.getenv("OPENAI_MAX_TOKENS", "4096"))

    # Audio Processing Configuration
    @property
    def whisper_model(self) -> str:
        return os.getenv("WHISPER_MODEL", "base.en")

    @property
    def audio_chunk_duration(self) -> int:
        return int(os.getenv("AUDIO_CHUNK_DURATION", "30"))

    # Performance Configuration
    @property
    def workers(self) -> int:
        # Number of worker processes for production
        default_workers = "1" if self.is_development else "4"
        return int(os.getenv("WORKERS", default_workers))

    @property
    def max_concurrent_requests(self) -> int:
        default_max = "10" if self.is_development else "100"
        return int(os.getenv("MAX_CONCURRENT_REQUESTS", default_max))


# Global settings instance
settings = Settings()
