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
import jwt
from google.auth.transport import requests
from google.oauth2 import id_token
from fastapi import HTTPException, status
from config import Settings

logger = logging.getLogger(__name__)


class UserAuthManager:
    """Manages user authentication and session management"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.jwt_secret = self._get_jwt_secret()
        self.jwt_algorithm = "HS256"
        self.token_expire_hours = 24 * 7  # 7 days

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
        # Create token payload
        payload = {
            "user_id": user_info["user_id"],
            "email": user_info["email"],
            "name": user_info["name"],
            "provider": user_info["provider"],
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc)
            + timedelta(hours=self.token_expire_hours),
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
            payload = jwt.decode(
                token, self.jwt_secret, algorithms=[self.jwt_algorithm]
            )

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
