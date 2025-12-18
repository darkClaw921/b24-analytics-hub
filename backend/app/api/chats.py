"""
Chats API endpoints
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select

from app.dependencies import CurrentUser, DBSession
from app.models import Chat, Message, ChatContext

router = APIRouter(prefix="/api/chats", tags=["chats"])


class ChatCreate(BaseModel):
    title: str


class ChatResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    total_tokens: Optional[int] = 0
    
    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    tool_name: Optional[str] = None
    tokens_used: int
    created_at: datetime
    
    class Config:
        from_attributes = True


@router.get("", response_model=List[ChatResponse])
async def get_chats(current_user: CurrentUser, db: DBSession):
    """
    Get all chats for current user
    """
    result = await db.execute(
        select(Chat)
        .where(Chat.user_id == current_user.id)
        .order_by(Chat.updated_at.desc())
    )
    chats = result.scalars().all()
    
    # Add total_tokens to each chat
    chat_responses = []
    for chat in chats:
        context_result = await db.execute(
            select(ChatContext).where(ChatContext.chat_id == chat.id)
        )
        context = context_result.scalar_one_or_none()
        
        chat_data = {
            "id": chat.id,
            "title": chat.title,
            "created_at": chat.created_at,
            "updated_at": chat.updated_at,
            "total_tokens": context.total_tokens if context else 0
        }
        chat_responses.append(chat_data)
    
    return chat_responses


@router.post("", response_model=ChatResponse)
async def create_chat(chat_data: ChatCreate, current_user: CurrentUser, db: DBSession):
    """
    Create a new chat
    """
    chat = Chat(
        user_id=current_user.id,
        title=chat_data.title
    )
    
    db.add(chat)
    await db.flush()
    await db.refresh(chat)
    
    # Create chat context
    context = ChatContext(chat_id=chat.id, total_tokens=0)
    db.add(context)
    
    await db.commit()
    
    return {
        "id": chat.id,
        "title": chat.title,
        "created_at": chat.created_at,
        "updated_at": chat.updated_at,
        "total_tokens": 0
    }


@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat(chat_id: int, current_user: CurrentUser, db: DBSession):
    """
    Get chat by ID
    """
    result = await db.execute(
        select(Chat).where(Chat.id == chat_id, Chat.user_id == current_user.id)
    )
    chat = result.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    
    # Get context
    context_result = await db.execute(
        select(ChatContext).where(ChatContext.chat_id == chat.id)
    )
    context = context_result.scalar_one_or_none()
    
    return {
        "id": chat.id,
        "title": chat.title,
        "created_at": chat.created_at,
        "updated_at": chat.updated_at,
        "total_tokens": context.total_tokens if context else 0
    }


@router.delete("/{chat_id}")
async def delete_chat(chat_id: int, current_user: CurrentUser, db: DBSession):
    """
    Delete chat
    """
    result = await db.execute(
        select(Chat).where(Chat.id == chat_id, Chat.user_id == current_user.id)
    )
    chat = result.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    
    # Delete chat (cascade will delete messages and context automatically)
    await db.delete(chat)
    await db.commit()
    
    return {"message": "Chat deleted successfully"}


@router.get("/{chat_id}/messages", response_model=List[MessageResponse])
async def get_messages(chat_id: int, current_user: CurrentUser, db: DBSession):
    """
    Get messages for a chat
    """
    # Verify chat belongs to user
    result = await db.execute(
        select(Chat).where(Chat.id == chat_id, Chat.user_id == current_user.id)
    )
    chat = result.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    
    # Get messages
    messages_result = await db.execute(
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at)
    )
    messages = messages_result.scalars().all()
    
    return messages

