"""
Chat and Message models
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class MessageRole(str, enum.Enum):
    """Message role enum"""
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Chat(Base):
    """Chat model for storing conversation threads"""
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan", order_by="Message.created_at")
    context = relationship("ChatContext", back_populates="chat", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Chat(id={self.id}, title='{self.title}', user_id={self.user_id})>"


class Message(Base):
    """Message model for storing chat messages"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    tool_name = Column(String(255), nullable=True)
    tool_arguments = Column(JSON, nullable=True)
    tokens_used = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    chat = relationship("Chat", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, chat_id={self.chat_id}, role='{self.role}')>"


class ChatContext(Base):
    """Chat context model for tracking token usage"""
    __tablename__ = "chat_contexts"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), unique=True, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    chat = relationship("Chat", back_populates="context")

    def __repr__(self):
        return f"<ChatContext(chat_id={self.chat_id}, total_tokens={self.total_tokens})>"

