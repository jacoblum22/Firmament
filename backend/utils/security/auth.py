"""
User Authentication with Google OAuth for StudyMate-v2

This module handles user authentication using Google OAuth 2.0.
It supports session management and user data isolation.
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from uuid import uuid4
import jwt
import redis
from google.auth.transport import requests
from google.oauth2 import id_token
from fastapi import HTTPException, status
from app.config import Settings

logger = logging.getLogger(__name__)


class UserAuthManager:
    """Manages user authentication and session management"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.jwt_secret = self._get_jwt_secret()
        self.jwt_algorithm = "HS256"
        self.token_expire_hours = self.settings.token_expiry_hours
        self.redis_client: Optional[redis.Redis] = None
        self._blacklist_key_prefix = "token_blacklist:"
        self.blacklisted_jtis: set[str] = set()
        self.blacklisted_jti_expiries: dict[str, int] = {}
        self._last_blacklist_cleanup = datetime.now(timezone.utc)
        self._blacklist_cleanup_interval_seconds = 600
        self._initialize_blacklist_storage()

    def _initialize_blacklist_storage(self) -> None:
        """Initialize Redis-backed blacklist storage with in-memory fallback."""
        redis_url = self.settings.redis_url
        if not redis_url:
            logger.warning(
                "REDIS_URL not configured; using in-memory token blacklist fallback"
            )
            return

        try:
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            self.redis_client.ping()
            logger.info("Redis-backed token blacklist enabled")
        except Exception as exc:
            self.redis_client = None
            logger.warning(
                "Failed to connect to Redis for token blacklist: %s. "
                "Falling back to in-memory blacklist.",
                exc,
            )

    def _get_blacklist_key(self, jti: str) -> str:
        """Build Redis key for a token blacklist entry."""
        return f"{self._blacklist_key_prefix}{jti}"

    def _get_jwt_secret(self) -> str:
        """Get JWT secret key for token signing"""
        # Use dedicated JWT secret from configuration
        return self.settings.jwt_secret

    def verify_google_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify Google OAuth token and extract user information

        Args:
            token: Google OAuth token

        Returns:
            dict: User information if valid, None otherwise
        """
        try:
            # Verify the token with Google
            idinfo = id_token.verify_oauth2_token(
                token, requests.Request(), self.settings.google_client_id
            )

            # Validate the issuer
            if idinfo["iss"] not in [
                "accounts.google.com",
                "https://accounts.google.com",
            ]:
                logger.warning(f"Invalid token issuer: {idinfo['iss']}")
                return None

            # Extract user information
            user_info = {
                "user_id": idinfo["sub"],  # Google user ID (stable identifier)
                "email": idinfo["email"],
                "name": idinfo.get("name", ""),
                "picture": idinfo.get("picture", ""),
                "email_verified": idinfo.get("email_verified", False),
                "provider": "google",
            }

            logger.info(
                f"Successfully verified Google token for user: {user_info['email']}"
            )
            return user_info

        except ValueError as e:
            logger.warning(f"Invalid Google token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error verifying Google token: {e}")
            return None

    def create_session_token(self, user_info: Dict[str, Any]) -> str:
        """
        Create a JWT session token for the authenticated user

        Args:
            user_info: User information from authentication

        Returns:
            str: JWT session token
        """
        now = datetime.now(timezone.utc)
        token_expiry = now + timedelta(hours=self.token_expire_hours)
        token_jti = str(uuid4())

        # Create token payload
        payload = {
            "user_id": user_info["user_id"],
            "email": user_info["email"],
            "name": user_info["name"],
            "provider": user_info["provider"],
            "iat": now,
            "exp": token_expiry,
            "jti": token_jti,
        }

        # Generate JWT token
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

        logger.info(f"Created session token for user: {user_info['email']}")
        return token

    def verify_session_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a session token

        Args:
            token: JWT session token

        Returns:
            dict: User information if valid, None otherwise
        """
        try:
            self._cleanup_blacklisted_tokens()
            payload = jwt.decode(
                token, self.jwt_secret, algorithms=[self.jwt_algorithm]
            )

            jti = payload.get("jti")
            if jti and self.is_token_blacklisted(jti):
                logger.warning("Session token has been invalidated")
                return None

            # Check if token is expired (JWT library should handle this, but double-check)
            exp = payload.get("exp")
            if exp and datetime.now(timezone.utc) > datetime.fromtimestamp(
                exp, tz=timezone.utc
            ):
                logger.warning("Session token expired")
                return None

            logger.debug(
                f"Successfully verified session token for user: {payload['email']}"
            )
            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("Session token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid session token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error verifying session token: {e}")
            return None

    def blacklist_token(self, jti: str, exp: Optional[int] = None) -> None:
        """Blacklist a JWT ID and optionally track its expiration for cleanup."""
        if not jti:
            return

        current_timestamp = int(datetime.now(timezone.utc).timestamp())

        if self.redis_client is not None:
            if exp is None:
                logger.warning(
                    "Token expiry not provided for JTI %s; using in-memory blacklist fallback",
                    jti,
                )
            else:
                try:
                    ttl_seconds = int(exp) - current_timestamp
                    if ttl_seconds > 0:
                        self.redis_client.setex(
                            self._get_blacklist_key(jti), ttl_seconds, "1"
                        )
                        return
                    logger.debug(
                        "Skipping blacklist entry for JTI %s because token is already expired",
                        jti,
                    )
                    return
                except Exception as exc:
                    logger.warning(
                        "Redis blacklist write failed for JTI %s: %s. Falling back to in-memory blacklist.",
                        jti,
                        exc,
                    )

        self.blacklisted_jtis.add(jti)
        if exp is not None:
            try:
                self.blacklisted_jti_expiries[jti] = int(exp)
            except (TypeError, ValueError):
                logger.warning("Unable to parse token expiry for blacklisted JTI")

        self._cleanup_blacklisted_tokens(force=False)

    def is_token_blacklisted(self, jti: str) -> bool:
        """Check if a JWT ID has been blacklisted."""
        if not jti:
            return False

        if self.redis_client is not None:
            try:
                if self.redis_client.exists(self._get_blacklist_key(jti)):
                    return True
            except Exception as exc:
                logger.warning(
                    "Redis blacklist read failed for JTI %s: %s. Falling back to in-memory blacklist.",
                    jti,
                    exc,
                )

        self._cleanup_blacklisted_tokens(force=False)
        return jti in self.blacklisted_jtis

    def _cleanup_blacklisted_tokens(self, force: bool = False) -> None:
        """Periodically remove blacklisted JTIs whose source token already expired."""
        now = datetime.now(timezone.utc)
        if (
            not force
            and (now - self._last_blacklist_cleanup).total_seconds()
            < self._blacklist_cleanup_interval_seconds
        ):
            return

        current_timestamp = int(now.timestamp())
        expired_jtis = [
            jti
            for jti, exp in self.blacklisted_jti_expiries.items()
            if exp <= current_timestamp
        ]

        for jti in expired_jtis:
            self.blacklisted_jtis.discard(jti)
            self.blacklisted_jti_expiries.pop(jti, None)

        self._last_blacklist_cleanup = now

    def get_user_content_hash(self, user_id: str, content: bytes) -> str:
        """
        Generate a user-specific content hash for hybrid sharing

        For hybrid sharing, we hash content without user ID so users can benefit
        from shared processing, but we'll store results in user-specific namespaces.

        Args:
            user_id: User identifier
            content: File content

        Returns:
            str: Content hash (same for all users with same content)
        """
        # For hybrid sharing, we use global content hash
        # This allows users to benefit from each other's processing
        return hashlib.sha256(content).hexdigest()

    def get_user_storage_path(
        self, user_id: str, content_hash: str, file_type: str
    ) -> str:
        """
        Generate a user-specific storage path for privacy

        Args:
            user_id: User identifier
            content_hash: Content hash
            file_type: Type of file (uploads, cache, temp)

        Returns:
            str: Storage path with user isolation
        """
        # Create user-specific path while maintaining content hash benefits
        if file_type == "uploads":
            return f"{self.settings.s3_uploads_prefix}users/{user_id}/{content_hash}/"
        elif file_type == "cache":
            return f"{self.settings.s3_cache_prefix}users/{user_id}/{content_hash}/"
        elif file_type == "temp":
            return f"{self.settings.s3_temp_prefix}users/{user_id}/{content_hash}/"
        else:
            return f"users/{user_id}/{content_hash}/"

    def get_shared_cache_path(self, content_hash: str) -> str:
        """
        Generate a shared cache path for content that can be safely shared

        This is for processed content that doesn't contain user-specific information
        but can benefit from shared processing (like transcriptions).

        Args:
            content_hash: Content hash

        Returns:
            str: Shared cache path
        """
        return f"{self.settings.s3_cache_prefix}shared/{content_hash}/"


# Global auth manager instance
_auth_manager: Optional[UserAuthManager] = None


def get_auth_manager() -> UserAuthManager:
    """Get the global auth manager instance"""
    global _auth_manager
    if _auth_manager is None:
        settings = Settings()
        _auth_manager = UserAuthManager(settings)
    return _auth_manager


def init_auth_manager(settings: Settings) -> UserAuthManager:
    """Initialize the global auth manager with specific settings"""
    global _auth_manager
    _auth_manager = UserAuthManager(settings)
    return _auth_manager


def blacklist_token(jti: str, exp: Optional[int] = None) -> None:
    """Blacklist a token JTI using the global auth manager."""
    get_auth_manager().blacklist_token(jti, exp)


def is_token_blacklisted(jti: str) -> bool:
    """Check if a token JTI is blacklisted using the global auth manager."""
    return get_auth_manager().is_token_blacklisted(jti)


# FastAPI dependency for requiring authentication
def require_authentication(token: Optional[str] = None) -> Dict[str, Any]:
    """
    FastAPI dependency that requires user authentication

    Args:
        token: JWT session token (from header or cookie)

    Returns:
        dict: User information

    Raises:
        HTTPException: If authentication fails
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    auth_manager = get_auth_manager()
    user_info = auth_manager.verify_session_token(token)

    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_info


def optional_authentication(token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    FastAPI dependency for optional authentication

    Args:
        token: JWT session token (from header or cookie)

    Returns:
        dict: User information if authenticated, None otherwise
    """
    if not token:
        return None

    auth_manager = get_auth_manager()
    return auth_manager.verify_session_token(token)
