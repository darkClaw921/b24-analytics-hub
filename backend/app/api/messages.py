"""
Messages API endpoints
"""
import json
import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
from sqlalchemy import select

from app.dependencies import CurrentUser, DBSession
from app.models import Chat, MessageRole, MCPTool
from app.services.chat_service import chat_service
from app.services.mcp_service import mcp_service
from app.services.token_service import token_service

logger = logging.getLogger(__name__)

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
        # IMPORTANT: Call tool through MCP with ORIGINAL data (tool_name and arguments keys)
        # Original tool_name and original parameter names are sent to backend
        tool_result = await mcp_service.call_tool(
            tool_data.server_name,
            tool_data.tool_name,  # Original tool name sent to MCP
            tool_data.arguments   # Original parameter names sent to MCP
        )
        
        # Format result to extract text content
        formatted_result = chat_service._format_mcp_result(tool_result)
        
        # Get tool display name and parameter display names from database for VISUAL DISPLAY ONLY
        # These are used only for user-facing messages, not for actual tool calls
        tool_display_name = tool_data.tool_name
        param_display_names = {}
        try:
            result = await db.execute(
                select(MCPTool).where(
                    MCPTool.tool_name == tool_data.tool_name,
                    MCPTool.is_active == True
                )
            )
            db_tool = result.scalar_one_or_none()
            if db_tool:
                # Get custom name for tool display (visual only)
                if db_tool.custom_name:
                    tool_display_name = db_tool.custom_name
                
                # Get parameter display names (visual only)
                param_display_names_raw = getattr(db_tool, 'parameter_display_names', None)
                if param_display_names_raw:
                    try:
                        param_display_names = json.loads(param_display_names_raw)
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.warning(f"Error parsing parameter_display_names for tool {tool_data.tool_name}: {e}")
        except Exception as e:
            logger.warning(f"Error loading tool display data: {e}")
        
        # Create user message describing the tool call with VISUAL tool name and parameter names
        # This is only for display purposes - original data was already sent to MCP above
        user_message_content = f"Вызов инструмента: {tool_display_name}"
        if tool_data.arguments:
            # Create display version of arguments with visual parameter names (for user message only)
            display_args = {}
            for original_key, value in tool_data.arguments.items():
                # Use visual name if available, otherwise use original
                # Preserve all spaces in display names (they are already trimmed on save, but internal spaces preserved)
                display_key = param_display_names.get(original_key, original_key)
                display_args[display_key] = value
            # Use ensure_ascii=False to preserve Unicode characters and proper spacing
            args_str = json.dumps(display_args, ensure_ascii=False, indent=None)
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
        
        # IMPORTANT: Save ORIGINAL tool_name and ORIGINAL arguments to database
        # Visual names are only used in user message above
        await chat_service.create_message(
            db,
            chat_id,
            MessageRole.TOOL,
            tool_message_content,
            tool_name=tool_data.tool_name,      # Original tool name saved
            tool_arguments=tool_data.arguments,  # Original parameter names saved
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

