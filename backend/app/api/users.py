"""
Users API endpoints
"""
from fastapi import APIRouter
from pydantic import BaseModel

from app.dependencies import CurrentUser

router = APIRouter(prefix="/api/users", tags=["users"])


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool
    
    class Config:
        from_attributes = True


@router.get("/me", response_model=UserResponse)
async def get_current_user(current_user: CurrentUser):
    """
    Get current authenticated user
    """
    return current_user

