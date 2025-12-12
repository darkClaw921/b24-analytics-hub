"""
Script to create first admin user
"""
import asyncio
import sys
import logging
from pathlib import Path

# Disable SQLAlchemy logging
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.database import AsyncSessionLocal, init_db
from app.services.user_service import UserService


async def create_admin():
    """Create first admin user"""
    await init_db()
    
    async with AsyncSessionLocal() as db:
        print("Создание первого администратора...")
        
        username = input("Имя пользователя: ").strip()
        email = input("Email: ").strip()
        password = input("Пароль: ").strip()
        
        if not username or not email or not password:
            print("Ошибка: все поля обязательны")
            return
        
        # Check if user already exists
        existing = await UserService.get_user_by_username(db, username)
        if existing:
            print(f"Ошибка: пользователь '{username}' уже существует")
            return
        
        existing_email = await UserService.get_user_by_email(db, email)
        if existing_email:
            print(f"Ошибка: email '{email}' уже используется")
            return
        
        # Create admin user
        user = await UserService.create_user(
            db,
            username,
            email,
            password,
            is_admin=True
        )
        
        await db.commit()
        
        print(f"\n✅ Администратор '{username}' успешно создан!")
        print(f"   ID: {user.id}")
        print(f"   Email: {user.email}")
        print(f"   Admin: {user.is_admin}")


if __name__ == "__main__":
    asyncio.run(create_admin())

