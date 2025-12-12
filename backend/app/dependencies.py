"""
FastAPI dependencies for authentication and database access
"""
import logging
from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.auth import decode_access_token
from app.models import User

logger = logging.getLogger(__name__)

# Security scheme for JWT bearer token
security = HTTPBearer(auto_error=False)


def get_token_from_header(request: Request) -> Optional[str]:
    """Extract token from Authorization header"""
    authorization = request.headers.get("Authorization")
    if not authorization:
        return None
    
    if not authorization.startswith("Bearer "):
        return None
    
    return authorization.replace("Bearer ", "", 1)


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """
    Dependency to get current authenticated user
    """
    # Try to get token from HTTPBearer first, then from header directly
    token = None
    if credentials:
        token = credentials.credentials
        logger.debug(f"Token from HTTPBearer: {token[:20] if token else 'None'}...")
    else:
        # Fallback: try to get token directly from header
        token = get_token_from_header(request)
        logger.debug(f"Token from header: {token[:20] if token else 'None'}...")
    
    if not token:
        logger.warning("No token provided in request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.debug(f"Attempting to decode token: {token[:20]}...")
    
    try:
        payload = decode_access_token(token)
    except HTTPException as e:
        logger.warning(f"Token decode failed: {e.detail}")
        raise
    
    user_id_raw = payload.get("sub")
    if user_id_raw is None:
        logger.warning("No user_id in token payload")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    # Ensure user_id is int
    try:
        user_id = int(user_id_raw)
        logger.debug(f"Looking up user with ID: {user_id}")
    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid user_id format: {user_id_raw}, error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token"
        )
    
    # Get user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        logger.warning(f"User with ID {user_id} not found in database")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    logger.debug(f"User authenticated: {user.username}")
    return user


async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Dependency to get current authenticated admin user
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return current_user


# Type aliases for easier use
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentAdminUser = Annotated[User, Depends(get_current_admin_user)]
DBSession = Annotated[AsyncSession, Depends(get_db)]

