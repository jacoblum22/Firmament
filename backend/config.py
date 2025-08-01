"""
Firmament Backend Configuration Management

This module provides a comprehensive configuration system for the Firmament backend,
supporting multiple deployment environments with proper security defaults and validation.

Key Features:
- Environment-specific configuration loading (.env.development, .env.production)
- Secure defaults that prioritize production security
- Comprehensive validation with detailed error messages
- Type hints for better IDE support and code reliability
- Flexible property-based access with runtime validation
- Support for both development and production deployment scenarios

Design Philosophy:
- Security by default: production settings are secure unless explicitly overridden
- Development convenience: development settings prioritize ease of use
- Fail fast: invalid configurations raise clear errors during startup
- Zero-config operation: sensible defaults for common scenarios
- Environment isolation: clear separation between dev/prod configurations

Configuration Priority (highest to lowest):
1. Environment variables
2. .env.{ENVIRONMENT} files
3. Default .env file
4. Hard-coded secure defaults

Security Considerations:
- Production secrets must be provided via environment variables
- Development uses insecure defaults for convenience
- API keys and JWT secrets are validated for minimum security requirements
- Database and external service credentials use secure defaults
- CORS and rate limiting are environment-appropriate

@author Firmament Development Team
@version 2.0.0
"""

import os
import sys
from typing import List, Optional
from dotenv import load_dotenv


class ConfigurationError(Exception):
    """
    Custom exception for configuration-related errors.

    Raised when:
    - Required environment variables are missing
    - Invalid configuration values are provided
    - Security requirements are not met
    - External service configuration is invalid
    """

    pass


class Settings:
    """
    Centralized configuration management for the Firmament backend.

    This class implements a property-based configuration system that:
    - Loads configuration from multiple sources in priority order
    - Validates configuration values at access time
    - Provides environment-specific defaults
    - Ensures security requirements are met

    Usage:
        settings = Settings()
        if settings.is_production:
            # Production-specific logic
            pass

        # Access configuration values
        db_url = settings.database_url
        api_key = settings.api_key
    """

    def __init__(self):
        """
        Initialize configuration by loading environment variables.

        Loading Strategy:
        1. Check for environment-specific file (.env.development, .env.production)
        2. Fall back to generic .env file
        3. Use environment variables as overrides
        4. Apply secure defaults
        """
        # Load environment-specific configuration first
        env_file = f".env.{os.getenv('ENVIRONMENT', 'development')}"
        if os.path.exists(env_file):
            load_dotenv(env_file)
            print(f"Loaded configuration from {env_file}")
        else:
            # Fallback to default .env file
            load_dotenv()
            print("Loaded configuration from default .env file")

    # Environment Detection Properties
    @property
    def environment(self) -> str:
        """Get the current deployment environment (development/production)."""
        return os.getenv("ENVIRONMENT", "development")

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"

    @property
    def debug(self) -> bool:
        """
        Get debug mode setting.

        Security: Debug is disabled by default in production to prevent
        information disclosure vulnerabilities.
        """
        # Debug should be False in production by default for security
        default_debug = "false" if self.is_production else "true"
        return os.getenv("DEBUG", default_debug).lower() == "true"

    # Server Configuration Properties
    @property
    def host(self) -> str:
        """
        Get server host binding address.

        Development: Binds to localhost (127.0.0.1) for security
        Production: Binds to all interfaces (0.0.0.0) for accessibility
        """
        return os.getenv("HOST", "127.0.0.1" if self.is_development else "0.0.0.0")

    @property
    def port(self) -> int:
        """
        Get server port number with validation.

        Validates that the port is within the valid range (1-65535)
        and handles deployment platform port assignment.
        """
        port_str = os.getenv("PORT", "8000")
        default_port = 8000

        try:
            port = int(port_str)
        except (ValueError, TypeError):
            if self.is_production:
                raise ConfigurationError(
                    f"Invalid PORT value '{port_str}'. Port must be a valid integer. "
                    f"Please check your environment configuration."
                )
            else:
                print(
                    f"⚠️  Warning: Invalid PORT value '{port_str}'. Using default port {default_port}."
                )
                return default_port

        # Validate port range
        if not (1 <= port <= 65535):
            if self.is_production:
                raise ConfigurationError(
                    f"Invalid PORT value {port}. Port must be between 1 and 65535. "
                    f"Please check your environment configuration."
                )
            else:
                print(
                    f"⚠️  Warning: Invalid PORT value {port}. Port must be between 1 and 65535. Using default port {default_port}."
                )
                return default_port

        return port

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
                "http://localhost:5174",  # Add port 5174 for Vite dev server
                "http://localhost:3000",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:5174",  # Add port 5174 for Vite dev server
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
    def jwt_secret(self) -> str:
        """Get JWT secret key for token signing and verification"""
        jwt_secret = os.getenv("JWT_SECRET", "").strip()

        if not jwt_secret:
            if self.is_production:
                raise ConfigurationError(
                    "JWT_SECRET is required in production. "
                    "Please set the JWT_SECRET environment variable to a secure random string."
                )
            else:
                # Development fallback with warning
                print("⚠️  Warning: JWT_SECRET is not set. Using development default.")
                return "dev-jwt-secret-change-in-production"

        # Check for placeholder values that should be replaced
        placeholder_patterns = [
            "CHANGE_ME",
            "change_me",
            "changeme",
            "placeholder",
            "PLACEHOLDER",
            "your_secret_here",
            "YOUR_SECRET_HERE",
        ]

        if any(pattern in jwt_secret for pattern in placeholder_patterns):
            if self.is_production:
                raise ConfigurationError(
                    f"JWT_SECRET contains placeholder text and must be replaced in production. "
                    f"Current value contains: {[p for p in placeholder_patterns if p in jwt_secret]}"
                )
            else:
                print(
                    "⚠️  Warning: JWT_SECRET contains placeholder text. Should be replaced for security."
                )

        # Validate JWT secret strength
        if len(jwt_secret) < 32:
            raise ConfigurationError(
                f"JWT_SECRET must be at least 32 characters long. Current length: {len(jwt_secret)}"
            )

        return jwt_secret

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

    # Redis Configuration
    @property
    def redis_url(self) -> Optional[str]:
        return os.getenv("REDIS_URL")

    @property
    def redis_host(self) -> str:
        return os.getenv("REDIS_HOST", "localhost")

    @property
    def redis_port(self) -> int:
        return int(os.getenv("REDIS_PORT", "6379"))

    @property
    def redis_db(self) -> int:
        return int(os.getenv("REDIS_DB", "0"))

    @property
    def redis_password(self) -> Optional[str]:
        return os.getenv("REDIS_PASSWORD")

    @property
    def enable_rate_limiting(self) -> bool:
        # Enable rate limiting in development for testing
        default_enable = "true" if self.is_development else "true"
        return os.getenv("ENABLE_RATE_LIMITING", default_enable).lower() == "true"

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
        size_str = os.getenv("UPLOAD_MAX_SIZE", default_size)

        try:
            size = int(size_str)
        except (ValueError, TypeError):
            if self.is_production:
                raise ConfigurationError(
                    f"Invalid UPLOAD_MAX_SIZE value '{size_str}'. Must be a valid integer representing bytes."
                )
            else:
                default_int = int(default_size)
                print(
                    f"⚠️  Warning: Invalid UPLOAD_MAX_SIZE value '{size_str}'. Using default {default_int // 1024 // 1024}MB."
                )
                return default_int

        # Validate size range (1MB to 1GB)
        min_size = 1024 * 1024  # 1MB
        max_size = 1024 * 1024 * 1024  # 1GB
        if not (min_size <= size <= max_size):
            if self.is_production:
                raise ConfigurationError(
                    f"UPLOAD_MAX_SIZE value {size} bytes ({size // 1024 // 1024}MB) is out of range. "
                    f"Must be between {min_size // 1024 // 1024}MB and {max_size // 1024 // 1024}MB."
                )
            else:
                default_int = int(default_size)
                print(
                    f"⚠️  Warning: UPLOAD_MAX_SIZE {size // 1024 // 1024}MB is out of range. Using default {default_int // 1024 // 1024}MB."
                )
                return default_int

        return size

    @property
    def upload_max_size_pdf(self) -> int:
        # PDF-specific size limit (default: 50MB dev, 100MB prod)
        default_size = "52428800" if self.is_development else "104857600"
        size_str = os.getenv("UPLOAD_MAX_SIZE_PDF", default_size)

        try:
            size = int(size_str)
        except (ValueError, TypeError):
            if self.is_production:
                raise ConfigurationError(
                    f"Invalid UPLOAD_MAX_SIZE_PDF value '{size_str}'. Must be a valid integer representing bytes."
                )
            else:
                default_int = int(default_size)
                print(
                    f"⚠️  Warning: Invalid UPLOAD_MAX_SIZE_PDF value '{size_str}'. Using default {default_int // 1024 // 1024}MB."
                )
                return default_int

        # Validate size range (1MB to 500MB for PDFs)
        min_size = 1024 * 1024  # 1MB
        max_size = 500 * 1024 * 1024  # 500MB
        if not (min_size <= size <= max_size):
            if self.is_production:
                raise ConfigurationError(
                    f"UPLOAD_MAX_SIZE_PDF value {size} bytes ({size // 1024 // 1024}MB) is out of range. "
                    f"Must be between {min_size // 1024 // 1024}MB and {max_size // 1024 // 1024}MB."
                )
            else:
                default_int = int(default_size)
                print(
                    f"⚠️  Warning: UPLOAD_MAX_SIZE_PDF {size // 1024 // 1024}MB is out of range. Using default {default_int // 1024 // 1024}MB."
                )
                return default_int

        return size

    @property
    def upload_max_size_audio(self) -> int:
        # Audio file size limit (default: 200MB dev, 300MB prod)
        default_size = (
            "209715200" if self.is_development else "314572800"
        )  # 200MB / 300MB
        size_str = os.getenv("UPLOAD_MAX_SIZE_AUDIO", default_size)

        try:
            size = int(size_str)
        except (ValueError, TypeError):
            if self.is_production:
                raise ConfigurationError(
                    f"Invalid UPLOAD_MAX_SIZE_AUDIO value '{size_str}'. Must be a valid integer representing bytes."
                )
            else:
                default_int = int(default_size)
                print(
                    f"⚠️  Warning: Invalid UPLOAD_MAX_SIZE_AUDIO value '{size_str}'. Using default {default_int // 1024 // 1024}MB."
                )
                return default_int

        # Validate size range (1MB to 1GB for audio)
        min_size = 1024 * 1024  # 1MB
        max_size = 1024 * 1024 * 1024  # 1GB
        if not (min_size <= size <= max_size):
            if self.is_production:
                raise ConfigurationError(
                    f"UPLOAD_MAX_SIZE_AUDIO value {size} bytes ({size // 1024 // 1024}MB) is out of range. "
                    f"Must be between {min_size // 1024 // 1024}MB and {max_size // 1024 // 1024}MB."
                )
            else:
                default_int = int(default_size)
                print(
                    f"⚠️  Warning: UPLOAD_MAX_SIZE_AUDIO {size // 1024 // 1024}MB is out of range. Using default {default_int // 1024 // 1024}MB."
                )
                return default_int

        return size

    @property
    def upload_max_size_wav(self) -> int:
        # WAV file size limit (default: 500MB dev, 800MB prod)
        default_size = (
            "524288000" if self.is_development else "838860800"
        )  # 500MB / 800MB
        size_str = os.getenv("UPLOAD_MAX_SIZE_WAV", default_size)

        try:
            size = int(size_str)
        except (ValueError, TypeError):
            if self.is_production:
                raise ConfigurationError(
                    f"Invalid UPLOAD_MAX_SIZE_WAV value '{size_str}'. Must be a valid integer representing bytes."
                )
            else:
                default_int = int(default_size)
                print(
                    f"⚠️  Warning: Invalid UPLOAD_MAX_SIZE_WAV value '{size_str}'. Using default {default_int // 1024 // 1024}MB."
                )
                return default_int

        # Validate size range (1MB to 2GB for WAV files)
        min_size = 1024 * 1024  # 1MB
        max_size = 2 * 1024 * 1024 * 1024  # 2GB
        if not (min_size <= size <= max_size):
            if self.is_production:
                raise ConfigurationError(
                    f"UPLOAD_MAX_SIZE_WAV value {size} bytes ({size // 1024 // 1024}MB) is out of range. "
                    f"Must be between {min_size // 1024 // 1024}MB and {max_size // 1024 // 1024}MB."
                )
            else:
                default_int = int(default_size)
                print(
                    f"⚠️  Warning: UPLOAD_MAX_SIZE_WAV {size // 1024 // 1024}MB is out of range. Using default {default_int // 1024 // 1024}MB."
                )
                return default_int

        return size

    @property
    def upload_max_size_text(self) -> int:
        # Text file size limit (default: 10MB dev, 20MB prod)
        default_size = "10485760" if self.is_development else "20971520"  # 10MB / 20MB
        size_str = os.getenv("UPLOAD_MAX_SIZE_TEXT", default_size)

        try:
            size = int(size_str)
        except (ValueError, TypeError):
            if self.is_production:
                raise ConfigurationError(
                    f"Invalid UPLOAD_MAX_SIZE_TEXT value '{size_str}'. Must be a valid integer representing bytes."
                )
            else:
                default_int = int(default_size)
                print(
                    f"⚠️  Warning: Invalid UPLOAD_MAX_SIZE_TEXT value '{size_str}'. Using default {default_int // 1024 // 1024}MB."
                )
                return default_int

        # Validate size range (100KB to 100MB for text files)
        min_size = 100 * 1024  # 100KB
        max_size = 100 * 1024 * 1024  # 100MB
        if not (min_size <= size <= max_size):
            if self.is_production:
                raise ConfigurationError(
                    f"UPLOAD_MAX_SIZE_TEXT value {size} bytes ({size // 1024}KB) is out of range. "
                    f"Must be between {min_size // 1024}KB and {max_size // 1024 // 1024}MB."
                )
            else:
                default_int = int(default_size)
                print(
                    f"⚠️  Warning: UPLOAD_MAX_SIZE_TEXT {size // 1024}KB is out of range. Using default {default_int // 1024 // 1024}MB."
                )
                return default_int

        return size

    @property
    def upload_allowed_extensions(self) -> list:
        # Allowed file extensions
        extensions_str = os.getenv("UPLOAD_ALLOWED_EXTENSIONS", "pdf,mp3,wav,txt,m4a")

        if not extensions_str or extensions_str.strip() == "":
            if self.is_production:
                raise ConfigurationError(
                    "UPLOAD_ALLOWED_EXTENSIONS cannot be empty. Please specify allowed file extensions."
                )
            else:
                print(
                    "⚠️  Warning: UPLOAD_ALLOWED_EXTENSIONS is empty. Using default extensions."
                )
                extensions_str = "pdf,mp3,wav,txt,m4a"

        try:
            extensions = [ext.strip().lower() for ext in extensions_str.split(",")]
            # Remove empty extensions
            extensions = [ext for ext in extensions if ext]

            if not extensions:
                if self.is_production:
                    raise ConfigurationError(
                        "UPLOAD_ALLOWED_EXTENSIONS contains no valid extensions after processing."
                    )
                else:
                    print(
                        "⚠️  Warning: No valid extensions found. Using default extensions."
                    )
                    return ["pdf", "mp3", "wav", "txt", "m4a"]

            # Validate extension format (no dots, alphanumeric + common chars)
            import re

            valid_ext_pattern = re.compile(r"^[a-z0-9]+$")
            invalid_extensions = [
                ext for ext in extensions if not valid_ext_pattern.match(ext)
            ]

            if invalid_extensions:
                if self.is_production:
                    raise ConfigurationError(
                        f"Invalid file extensions found: {invalid_extensions}. "
                        f"Extensions must contain only letters and numbers."
                    )
                else:
                    print(
                        f"⚠️  Warning: Invalid extensions removed: {invalid_extensions}"
                    )
                    extensions = [
                        ext for ext in extensions if valid_ext_pattern.match(ext)
                    ]

            # Warn if common extensions are missing in development
            if self.is_development:
                recommended_extensions = {"pdf", "mp3", "wav", "txt", "m4a"}
                missing_recommended = recommended_extensions - set(extensions)
                if missing_recommended:
                    print(
                        f"⚠️  Notice: Recommended extensions not included: {missing_recommended}"
                    )

            return extensions

        except Exception as e:
            if self.is_production:
                raise ConfigurationError(
                    f"Error processing UPLOAD_ALLOWED_EXTENSIONS: {e}"
                )
            else:
                print(f"⚠️  Warning: Error processing extensions: {e}. Using defaults.")
                return ["pdf", "mp3", "wav", "txt", "m4a"]

    @property
    def upload_validate_content(self) -> bool:
        # Whether to validate file content (signatures) - can be disabled for performance
        validate_str = os.getenv("UPLOAD_VALIDATE_CONTENT", "true").lower()

        if validate_str not in ["true", "false", "1", "0", "yes", "no"]:
            if self.is_production:
                raise ConfigurationError(
                    f"Invalid UPLOAD_VALIDATE_CONTENT value '{validate_str}'. "
                    f"Must be one of: true, false, 1, 0, yes, no"
                )
            else:
                print(
                    f"⚠️  Warning: Invalid UPLOAD_VALIDATE_CONTENT value '{validate_str}'. Using default 'true'."
                )
                validate_str = "true"

        # More permissive in development for faster testing
        if self.is_development and validate_str == "true":
            print(
                "💡 Tip: Set UPLOAD_VALIDATE_CONTENT=false in development to speed up file uploads during testing."
            )

        return validate_str in ["true", "1", "yes"]

    @property
    def upload_directory(self) -> str:
        # Directory for storing uploaded files
        directory = os.getenv("UPLOAD_DIRECTORY", "uploads").strip()

        if not directory:
            if self.is_production:
                raise ConfigurationError(
                    "UPLOAD_DIRECTORY cannot be empty. Please specify a valid directory path."
                )
            else:
                print("⚠️  Warning: UPLOAD_DIRECTORY is empty. Using default 'uploads'.")
                directory = "uploads"

        # Security validation: prevent path traversal
        if ".." in directory:
            raise ConfigurationError(
                f"UPLOAD_DIRECTORY '{directory}' contains path traversal sequences (..). "
                f"This is a security risk and not allowed."
            )

        # Prevent absolute paths for security
        if os.path.isabs(directory):
            if self.is_production:
                raise ConfigurationError(
                    f"UPLOAD_DIRECTORY '{directory}' is an absolute path. "
                    f"Please use relative paths for security."
                )
            else:
                print(
                    f"⚠️  Warning: UPLOAD_DIRECTORY '{directory}' is an absolute path. Consider using relative paths."
                )

        # Validate directory name format
        if (
            not directory.replace("_", "")
            .replace("-", "")
            .replace("/", "")
            .replace("\\", "")
            .isalnum()
        ):
            if self.is_production:
                raise ConfigurationError(
                    f"UPLOAD_DIRECTORY '{directory}' contains invalid characters. "
                    f"Use only letters, numbers, hyphens, underscores, and path separators."
                )
            else:
                print(
                    f"⚠️  Warning: UPLOAD_DIRECTORY '{directory}' contains potentially problematic characters."
                )

        return directory

    @property
    def temp_directory(self) -> str:
        # Directory for temporary file chunks during processing
        directory = os.getenv("TEMP_DIRECTORY", "temp_chunks").strip()

        if not directory:
            if self.is_production:
                raise ConfigurationError(
                    "TEMP_DIRECTORY cannot be empty. Please specify a valid directory path."
                )
            else:
                print(
                    "⚠️  Warning: TEMP_DIRECTORY is empty. Using default 'temp_chunks'."
                )
                directory = "temp_chunks"

        # Security validation: prevent path traversal
        if ".." in directory:
            raise ConfigurationError(
                f"TEMP_DIRECTORY '{directory}' contains path traversal sequences (..). "
                f"This is a security risk and not allowed."
            )

        # Prevent absolute paths for security
        if os.path.isabs(directory):
            if self.is_production:
                raise ConfigurationError(
                    f"TEMP_DIRECTORY '{directory}' is an absolute path. "
                    f"Please use relative paths for security."
                )
            else:
                print(
                    f"⚠️  Warning: TEMP_DIRECTORY '{directory}' is an absolute path. Consider using relative paths."
                )

        # Validate directory name format
        if (
            not directory.replace("_", "")
            .replace("-", "")
            .replace("/", "")
            .replace("\\", "")
            .isalnum()
        ):
            if self.is_production:
                raise ConfigurationError(
                    f"TEMP_DIRECTORY '{directory}' contains invalid characters. "
                    f"Use only letters, numbers, hyphens, underscores, and path separators."
                )
            else:
                print(
                    f"⚠️  Warning: TEMP_DIRECTORY '{directory}' contains potentially problematic characters."
                )

        return directory

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
        api_key = os.getenv("OPENAI_API_KEY", "").strip()

        # In production, OpenAI API key is required
        if self.is_production and not api_key:
            raise ConfigurationError(
                "OPENAI_API_KEY is required in production environment. "
                "Please set the OPENAI_API_KEY environment variable."
            )

        # In development, warn if missing but don't fail
        if self.is_development and not api_key:
            print(
                "⚠️  Warning: OPENAI_API_KEY is not set. OpenAI features will not work."
            )
            return ""

        # Validate API key format only if key is provided
        if api_key and len(api_key) > 0:
            if not api_key.startswith("sk-"):
                if self.is_production:
                    raise ConfigurationError(
                        "Invalid OPENAI_API_KEY format. OpenAI API keys should start with 'sk-'."
                    )
                else:
                    print(
                        "⚠️  Warning: OPENAI_API_KEY does not appear to be in the correct format."
                    )

        return api_key

    @property
    def openai_model(self) -> str:
        return os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    @property
    def openai_max_tokens(self) -> int:
        return int(os.getenv("OPENAI_MAX_TOKENS", "4096"))

    # AWS S3 Configuration
    @property
    def use_s3_storage(self) -> bool:
        """Whether to use S3 for file storage instead of local files"""
        # Default to True in production, False in development
        default_s3 = "true" if self.is_production else "false"
        return os.getenv("USE_S3_STORAGE", default_s3).lower() == "true"

    @property
    def aws_access_key_id(self) -> str:
        aws_key = os.getenv("AWS_ACCESS_KEY_ID", "").strip()

        if self.use_s3_storage and not aws_key:
            if self.is_production:
                raise ConfigurationError(
                    "AWS_ACCESS_KEY_ID is required when USE_S3_STORAGE is enabled. "
                    "Please set the AWS_ACCESS_KEY_ID environment variable."
                )
            else:
                print(
                    "⚠️  Warning: AWS_ACCESS_KEY_ID is not set. S3 storage will not work."
                )

        return aws_key

    @property
    def aws_secret_access_key(self) -> str:
        aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY", "").strip()

        if self.use_s3_storage and not aws_secret:
            if self.is_production:
                raise ConfigurationError(
                    "AWS_SECRET_ACCESS_KEY is required when USE_S3_STORAGE is enabled. "
                    "Please set the AWS_SECRET_ACCESS_KEY environment variable."
                )
            else:
                print(
                    "⚠️  Warning: AWS_SECRET_ACCESS_KEY is not set. S3 storage will not work."
                )

        return aws_secret

    @property
    def aws_region(self) -> str:
        """AWS region for S3 bucket"""
        return os.getenv("AWS_REGION", "us-east-1")

    @property
    def s3_bucket_name(self) -> str:
        """S3 bucket name for file storage"""
        bucket_name = os.getenv("S3_BUCKET_NAME", "").strip()

        if self.use_s3_storage and not bucket_name:
            if self.is_production:
                raise ConfigurationError(
                    "S3_BUCKET_NAME is required when USE_S3_STORAGE is enabled. "
                    "Please set the S3_BUCKET_NAME environment variable."
                )
            else:
                print(
                    "⚠️  Warning: S3_BUCKET_NAME is not set. S3 storage will not work."
                )

        return bucket_name

    @property
    def s3_uploads_prefix(self) -> str:
        """S3 prefix for uploaded files"""
        return os.getenv("S3_UPLOADS_PREFIX", "uploads/")

    @property
    def s3_cache_prefix(self) -> str:
        """S3 prefix for cached/processed files"""
        return os.getenv("S3_CACHE_PREFIX", "cache/")

    @property
    def s3_temp_prefix(self) -> str:
        """S3 prefix for temporary files"""
        return os.getenv("S3_TEMP_PREFIX", "temp/")

    # Google OAuth Configuration
    @property
    def google_client_id(self) -> str:
        """Google OAuth client ID"""
        client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()

        if self.is_production and not client_id:
            raise ConfigurationError(
                "GOOGLE_CLIENT_ID is required in production environment. "
                "Please set the GOOGLE_CLIENT_ID environment variable."
            )
        elif self.is_development and not client_id:
            print(
                "⚠️  Warning: GOOGLE_CLIENT_ID is not set. Google OAuth will not work."
            )

        return client_id

    @property
    def google_client_secret(self) -> str:
        """Google OAuth client secret"""
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()

        if self.is_production and not client_secret:
            raise ConfigurationError(
                "GOOGLE_CLIENT_SECRET is required in production environment. "
                "Please set the GOOGLE_CLIENT_SECRET environment variable."
            )
        elif self.is_development and not client_secret:
            print(
                "⚠️  Warning: GOOGLE_CLIENT_SECRET is not set. Google OAuth will not work."
            )

        return client_secret

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

    def validate_configuration(self) -> None:
        """
        Validate critical configuration settings.
        Raises ConfigurationError for missing required settings in production.
        """
        errors = []
        warnings = []

        # Critical validation for production
        if self.is_production:
            # OpenAI API Key validation
            api_key = os.getenv("OPENAI_API_KEY", "").strip()

            if not api_key:
                errors.append(
                    "OPENAI_API_KEY is required in production environment. "
                    "Please set the OPENAI_API_KEY environment variable."
                )
            elif api_key.startswith("CHANGE_ME"):
                errors.append(
                    "OPENAI_API_KEY contains placeholder value 'CHANGE_ME'. "
                    "Please set a valid OpenAI API key."
                )
            elif not api_key.startswith("sk-"):
                errors.append(
                    "Invalid OPENAI_API_KEY format. OpenAI API keys should start with 'sk-'."
                )

            # Check for placeholder values in production
            if "your-domain.com" in str(self.allowed_origins):
                errors.append(
                    "ALLOWED_ORIGINS contains placeholder values. "
                    "Please update with your actual domain."
                )

            api_key_env = os.getenv("API_KEY", "")
            if not api_key_env:
                warnings.append("API_KEY is not set. API authentication will not work.")
            elif "CHANGE_ME" in api_key_env:
                errors.append(
                    "API_KEY contains placeholder value 'CHANGE_ME'. "
                    "Please set a secure API key."
                )

            # Redis configuration for production rate limiting
            redis_password = os.getenv("REDIS_PASSWORD", "")
            if redis_password and "CHANGE_ME" in redis_password:
                errors.append(
                    "REDIS_PASSWORD contains placeholder value 'CHANGE_ME'. "
                    "Please set a secure Redis password."
                )

            # Database configuration check
            postgres_password = os.getenv("POSTGRES_PASSWORD", "")
            if postgres_password and "CHANGE_ME" in postgres_password:
                errors.append(
                    "POSTGRES_PASSWORD contains placeholder value 'CHANGE_ME'. "
                    "Please set a secure database password."
                )

            if self.enable_rate_limiting and not self.redis_url and not self.redis_host:
                warnings.append(
                    "Rate limiting is enabled but no Redis configuration found. "
                    "This may cause performance issues."
                )

            if not self.database_url:
                warnings.append(
                    "DATABASE_URL is not set. Database features will not work."
                )

        # Development warnings
        elif self.is_development:
            # Check for missing OpenAI key (already handled in property)
            _ = self.openai_api_key  # This will print warning if missing

            if not self.redis_url and not self.redis_host:
                warnings.append(
                    "Redis not configured. Rate limiting will use in-memory fallback."
                )

        # Port validation (all environments)
        if not (1 <= self.port <= 65535):
            errors.append(
                f"Invalid port number: {self.port}. Must be between 1 and 65535."
            )

        # Worker count validation
        if self.workers < 1:
            errors.append(f"Invalid worker count: {self.workers}. Must be at least 1.")

        # File upload configuration validation
        # Access properties to trigger their enhanced validation
        try:
            # Validate all file size limits by accessing them
            _ = self.upload_max_size
            _ = self.upload_max_size_pdf
            _ = self.upload_max_size_audio
            _ = self.upload_max_size_wav
            _ = self.upload_max_size_text

            # Validate other upload configurations
            _ = self.upload_allowed_extensions
            _ = self.upload_validate_content
            _ = self.upload_directory
            _ = self.temp_directory

            # Additional logical validation
            if self.upload_max_size_pdf > self.upload_max_size:
                warnings.append(
                    f"PDF size limit ({self.upload_max_size_pdf // 1024 // 1024}MB) is larger than "
                    f"general upload limit ({self.upload_max_size // 1024 // 1024}MB)."
                )

            if self.upload_max_size_text > self.upload_max_size:
                warnings.append(
                    f"Text size limit ({self.upload_max_size_text // 1024 // 1024}MB) is larger than "
                    f"general upload limit ({self.upload_max_size // 1024 // 1024}MB)."
                )

            if len(self.upload_allowed_extensions) == 0:
                errors.append("No file extensions are allowed for upload.")

        except ConfigurationError as e:
            # ConfigurationError from properties should bubble up
            raise e
        except Exception as e:
            errors.append(f"File upload configuration validation failed: {e}")
        # Report errors and warnings
        if warnings:
            print("⚠️  Configuration Warnings:")
            for warning in warnings:
                print(f"   • {warning}")

        if errors:
            error_message = "❌ Configuration Errors:\n" + "\n".join(
                f"   • {error}" for error in errors
            )
            if self.is_production:
                error_message += "\n\n💡 To fix these issues:"
                error_message += "\n   • Run: python setup_production.py"
                error_message += "\n   • Or manually update the placeholder values in .env.production"
                error_message += "\n   • Ensure all CHANGE_ME_ values are replaced with secure values"
            raise ConfigurationError(error_message)

        print(f"✅ Configuration validation passed for {self.environment} environment")

    def get_config_summary(self) -> dict:
        """Get a summary of current configuration (safe for logging)"""
        return {
            "environment": self.environment,
            "debug": self.debug,
            "host": self.host,
            "port": self.port,
            "workers": self.workers,
            "cors_origins_count": len(self.allowed_origins),
            "rate_limiting_enabled": self.enable_rate_limiting,
            "redis_configured": bool(self.redis_url or self.redis_host),
            "openai_configured": bool(self.openai_api_key),
            "database_configured": bool(self.database_url),
            "upload_max_size_mb": round(self.upload_max_size / 1024 / 1024, 1),
            "log_level": self.log_level,
        }


# Global settings instance
settings = Settings()

# Automatically validate configuration on import
# This ensures that configuration errors are caught early
try:
    settings.validate_configuration()
except ConfigurationError as e:
    print(f"\n{e}")
    print("\n💡 Please check your environment configuration and try again.")
    if settings.is_production:
        print("🚨 Application cannot start with invalid production configuration.")
        sys.exit(1)
    else:
        print("⚠️  Development mode: Continuing with warnings...")
