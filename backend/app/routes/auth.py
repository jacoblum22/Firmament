from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from utils.security.auth import get_auth_manager

router = APIRouter(prefix="/auth", tags=["auth"])


class GoogleAuthRequest(BaseModel):
    token: str


class AuthResponse(BaseModel):
    success: bool
    session_token: str
    user_info: Dict[str, Any]


class TokenRefreshResponse(BaseModel):
    success: bool
    session_token: str


class UserInfo(BaseModel):
    user_id: str
    email: str
    name: str
    picture: str


security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Optional[Dict[str, Any]]:
    """Get current user from JWT token"""
    if not credentials:
        return None

    auth_manager = get_auth_manager()
    return auth_manager.verify_session_token(credentials.credentials)


def get_current_user_required(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """Get current user from JWT token (required)"""
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    auth_manager = get_auth_manager()
    user_info = auth_manager.verify_session_token(credentials.credentials)

    if not user_info:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_info


@router.post("/google", response_model=AuthResponse)
async def authenticate_with_google(request: GoogleAuthRequest):
    """
    Authenticate user with Google OAuth token
    """
    auth_manager = get_auth_manager()

    user_info = auth_manager.verify_google_token(request.token)
    if not user_info:
        raise HTTPException(
            status_code=400, detail="Invalid Google authentication token"
        )

    session_token = auth_manager.create_session_token(user_info)

    return AuthResponse(success=True, session_token=session_token, user_info=user_info)


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user_required),
):
    """
    Get current authenticated user information
    """
    return UserInfo(
        user_id=current_user["user_id"],
        email=current_user["email"],
        name=current_user["name"],
        picture=current_user.get("picture", ""),
    )


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Refresh a valid session token and invalidate the old one.
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    auth_manager = get_auth_manager()
    current_payload = auth_manager.verify_session_token(credentials.credentials)
    if not current_payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    current_jti = current_payload.get("jti")
    current_exp = current_payload.get("exp")
    if current_jti:
        auth_manager.blacklist_token(current_jti, current_exp)

    refreshed_token = auth_manager.create_session_token(current_payload)
    return TokenRefreshResponse(success=True, session_token=refreshed_token)


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Logout user and invalidate current token.
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    auth_manager = get_auth_manager()
    payload = auth_manager.verify_session_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    jti = payload.get("jti")
    exp = payload.get("exp")
    if jti:
        auth_manager.blacklist_token(jti, exp)

    return {"success": True, "message": "Logged out successfully"}

