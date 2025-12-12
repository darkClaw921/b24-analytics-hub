"""
Messages API endpoints
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
from sqlalchemy import select

from app.dependencies import CurrentUser, DBSession
from app.models import Chat, MessageRole
from app.services.chat_service import chat_service
from app.services.mcp_service import mcp_service
from app.services.token_service import token_service

router = APIRouter(prefix="/api/chats", tags=["messages"])


class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    message: str
    tokens_used: int
    tool_calls: bool


@router.post("/{chat_id}/messages", response_model=MessageResponse)
async def send_message(
    chat_id: int,
    message_data: MessageCreate,
    current_user: CurrentUser,
    db: DBSession
):
    """
    Send a message to chat and get LLM response
    """
    # Verify chat belongs to user
    result = await db.execute(
        select(Chat).where(Chat.id == chat_id, Chat.user_id == current_user.id)
    )
    chat = result.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    
    # Send message and get response
    try:
        response = await chat_service.send_message(
            db,
            chat_id,
            message_data.content
        )
        
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}"
        )


class ToolCallRequest(BaseModel):
    server_name: str
    tool_name: str
    arguments: Dict[str, Any]


@router.post("/{chat_id}/call-tool")
async def call_tool_in_chat(
    chat_id: int,
    tool_data: ToolCallRequest,
    current_user: CurrentUser,
    db: DBSession
):
    """
    Call MCP tool and save result to chat
    """
    # Verify chat belongs to user
    result = await db.execute(
        select(Chat).where(Chat.id == chat_id, Chat.user_id == current_user.id)
    )
    chat = result.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    
    try:
        # Call tool through MCP
        tool_result = await mcp_service.call_tool(
            tool_data.server_name,
            tool_data.tool_name,
            tool_data.arguments
        )
        
        # Format result to extract text content
        formatted_result = chat_service._format_mcp_result(tool_result)
        
        # Create user message describing the tool call
        user_message_content = f"Вызов инструмента: {tool_data.tool_name}"
        if tool_data.arguments:
            import json
            args_str = json.dumps(tool_data.arguments, ensure_ascii=False)
            user_message_content += f"\nПараметры: {args_str}"
        
        await chat_service.create_message(
            db,
            chat_id,
            MessageRole.USER,
            user_message_content,
            tokens_used=token_service.count_tokens(user_message_content)
        )
        
        # Save tool result message (just the formatted text, no markdown wrapper)
        tool_message_content = formatted_result
        
        await chat_service.create_message(
            db,
            chat_id,
            MessageRole.TOOL,
            tool_message_content,
            tool_name=tool_data.tool_name,
            tool_arguments=tool_data.arguments,
            tokens_used=token_service.count_tokens(tool_message_content)
        )
        
        await db.commit()
        
        return {
            "success": True,
            "result": tool_result,
            "message": tool_message_content
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calling tool: {str(e)}"
        )

