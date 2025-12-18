"""
Database configuration and session management
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Disable SQLAlchemy engine logging
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./b24_analytics.db")

# Create async engine (echo=False to disable SQL logging)
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


async def get_db() -> AsyncSession:
    """
    Dependency for getting async database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database - tables are created by Alembic migrations"""
    # Don't create tables here - let Alembic handle migrations
    # This function is kept for compatibility but does nothing
    # All table creation should be done through Alembic migrations
    pass

