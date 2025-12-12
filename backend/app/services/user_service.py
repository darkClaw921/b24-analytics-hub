"""
User service for user management operations
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.models import User
from app.auth import get_password_hash, verify_password


class UserService:
    """Service for user management"""
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by ID"""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """Get user by username"""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_user(
        db: AsyncSession,
        username: str,
        email: str,
        password: str,
        is_admin: bool = False
    ) -> User:
        """
        Create a new user
        
        Args:
            db: Database session
            username: Username
            email: Email
            password: Plain password (will be hashed)
            is_admin: Whether user is admin
        
        Returns:
            Created user
        """
        password_hash = get_password_hash(password)
        
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            is_admin=is_admin
        )
        
        db.add(user)
        await db.flush()
        await db.refresh(user)
        
        return user
    
    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        username: str,
        password: str
    ) -> Optional[User]:
        """
        Authenticate user with username and password
        
        Args:
            db: Database session
            username: Username
            password: Plain password
        
        Returns:
            User if authentication successful, None otherwise
        """
        user = await UserService.get_user_by_username(db, username)
        
        if not user:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
        
        return user
    
    @staticmethod
    async def get_all_users(db: AsyncSession) -> list[User]:
        """Get all users"""
        result = await db.execute(select(User))
        return result.scalars().all()
    
    @staticmethod
    async def delete_user(db: AsyncSession, user_id: int) -> bool:
        """
        Delete user
        
        Returns:
            True if user was deleted, False if not found
        """
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            return False
        
        await db.delete(user)
        return True

