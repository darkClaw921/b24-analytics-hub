"""
Chat service for managing conversations with OpenAI and MCP tools
"""
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import json

from app.config import settings
from app.models import Chat, Message, MessageRole, ChatContext, MCPServer, MCPTool
from app.services.mcp_service import mcp_service
from app.services.token_service import token_service

logger = logging.getLogger(__name__)


class ChatService:
    """Service for managing chat conversations with LLM and MCP tools"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o-mini"
    
    async def get_chat_history(
        self,
        db: AsyncSession,
        chat_id: int,
        limit: Optional[int] = None
    ) -> List[Message]:
        """
        Get chat message history
        
        Args:
            db: Database session
            chat_id: Chat ID
            limit: Optional limit on number of messages
        
        Returns:
            List of messages ordered by creation time
        """
        query = select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at)
        
        if limit:
            query = query.limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def create_message(
        self,
        db: AsyncSession,
        chat_id: int,
        role: MessageRole,
        content: str,
        tool_name: Optional[str] = None,
        tool_arguments: Optional[Dict[str, Any]] = None,
        tokens_used: int = 0
    ) -> Message:
        """
        Create a new message in chat
        
        Args:
            db: Database session
            chat_id: Chat ID
            role: Message role
            content: Message content
            tool_name: Optional tool name if message is tool result
            tool_arguments: Optional tool arguments
            tokens_used: Number of tokens used
        
        Returns:
            Created message
        """
        message = Message(
            chat_id=chat_id,
            role=role,
            content=content,
            tool_name=tool_name,
            tool_arguments=tool_arguments,
            tokens_used=tokens_used
        )
        
        db.add(message)
        await db.flush()
        await db.refresh(message)
        
        # Update chat context total tokens
        await self._update_chat_context(db, chat_id, tokens_used)
        
        return message
    
    async def _update_chat_context(
        self,
        db: AsyncSession,
        chat_id: int,
        tokens_delta: int
    ):
        """Update chat context with new token count"""
        result = await db.execute(
            select(ChatContext).where(ChatContext.chat_id == chat_id)
        )
        context = result.scalar_one_or_none()
        
        if not context:
            context = ChatContext(chat_id=chat_id, total_tokens=tokens_delta)
            db.add(context)
        else:
            context.total_tokens += tokens_delta
        
        await db.flush()
    
    async def send_message(
        self,
        db: AsyncSession,
        chat_id: int,
        user_message: str,
        active_tool_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send a message and get LLM response with MCP tools
        
        Args:
            db: Database session
            chat_id: Chat ID
            user_message: User message text
            active_tool_names: Optional list of active tool names (for filtering)
        
        Returns:
            Dict with assistant_message, tokens_used, and tool_calls info
        """
        # Save user message
        user_msg = await self.create_message(
            db,
            chat_id,
            MessageRole.USER,
            user_message,
            tokens_used=token_service.count_tokens(user_message)
        )
        
        # Get chat history
        history = await self.get_chat_history(db, chat_id)
        
        # Build messages for OpenAI
        messages = self._build_messages_for_api(history)
        
        # Get MCP tools
        tools = await mcp_service.get_tools()
        
        # Filter tools if active_tool_names provided
        if active_tool_names:
            tools = [t for t in tools if t.name in active_tool_names]
        
        # Convert tools to OpenAI format and filter out invalid ones
        openai_tools = []
        for tool in tools:
            try:
                openai_tool = self._tool_to_openai_format(tool)
                # Validate that parameters schema is valid
                params = openai_tool["function"]["parameters"]
                if isinstance(params, dict) and params.get("type") == "object":
                    openai_tools.append(openai_tool)
                else:
                    logger.warning(f"Skipping tool {tool.name}: invalid parameters schema")
            except Exception as e:
                logger.warning(f"Skipping tool {tool.name}: error converting to OpenAI format: {e}")
        
        try:
            # Call OpenAI with tools
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=openai_tools if openai_tools else None,
                tool_choice="auto" if openai_tools else None,
            )
            
            # Get response message
            response_message = response.choices[0].message
            
            # Calculate tokens used (from response or estimate)
            tokens_used = 0
            if hasattr(response, "usage") and response.usage:
                tokens_used = response.usage.total_tokens
            else:
                tokens_used = token_service.count_message_tokens(messages)
                tokens_used += token_service.count_tokens(response_message.content or "")
            
            # Handle tool calls if present
            if response_message.tool_calls:
                tool_results = []
                
                for tool_call in response_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    # Find server name for this tool from database
                    server_name = None
                    
                    # First try to get from tool metadata if available
                    for tool in tools:
                        if tool.name == tool_name:
                            server_name = getattr(tool, "server_name", None)
                            break
                    
                    # If not found in metadata, search in database
                    if not server_name:
                        try:
                            result = await db.execute(
                                select(MCPTool, MCPServer)
                                .join(MCPServer, MCPTool.server_id == MCPServer.id)
                                .where(
                                    MCPTool.tool_name == tool_name,
                                    MCPTool.is_active == True,
                                    MCPServer.is_active == True
                                )
                            )
                            tool_server = result.first()
                            if tool_server:
                                server_name = tool_server.MCPServer.name
                        except Exception as e:
                            logger.warning(f"Error finding server for tool {tool_name}: {e}")
                    
                    # Fallback: try to find any active server that has this tool
                    if not server_name:
                        try:
                            # Get all active servers and try to find the tool
                            result = await db.execute(
                                select(MCPServer).where(MCPServer.is_active == True)
                            )
                            active_servers = result.scalars().all()
                            
                            # Try each server to find the tool
                            for server in active_servers:
                                try:
                                    # Check if tool exists in this server by trying to get tools
                                    server_tools = await mcp_service.get_tools(server_name=server.name)
                                    if any(t.name == tool_name for t in server_tools):
                                        server_name = server.name
                                        break
                                except Exception:
                                    continue
                        except Exception as e:
                            logger.warning(f"Error searching for tool {tool_name} in active servers: {e}")
                    
                    # Last resort: use first active server name from DB
                    if not server_name:
                        try:
                            result = await db.execute(
                                select(MCPServer).where(MCPServer.is_active == True).limit(1)
                            )
                            server = result.scalar_one_or_none()
                            if server:
                                server_name = server.name
                        except Exception as e:
                            logger.warning(f"Error getting default server: {e}")
                    
                    if not server_name:
                        raise Exception(f"Could not find server for tool {tool_name}")
                    
                    # Call tool through MCP
                    try:
                        tool_result = await mcp_service.call_tool(
                            server_name,
                            tool_name,
                            tool_args
                        )
                        
                        # Format result to extract text content
                        formatted_result = self._format_mcp_result(tool_result)
                        
                        # Save tool call message
                        await self.create_message(
                            db,
                            chat_id,
                            MessageRole.TOOL,
                            formatted_result,
                            tool_name=tool_name,
                            tool_arguments=tool_args,
                            tokens_used=token_service.count_tokens(formatted_result)
                        )
                        
                        tool_results.append({
                            "tool_name": tool_name,
                            "result": tool_result
                        })
                    except Exception as e:
                        logger.error(f"Error calling tool {tool_name}: {e}")
                        tool_results.append({
                            "tool_name": tool_name,
                            "error": str(e)
                        })
                
                # Build final response with tool results
                assistant_content = response_message.content or ""
                if tool_results:
                    assistant_content += "\n\n" + self._format_tool_results(tool_results)
            else:
                assistant_content = response_message.content or ""
            
            # Save assistant message
            assistant_msg = await self.create_message(
                db,
                chat_id,
                MessageRole.ASSISTANT,
                assistant_content,
                tokens_used=tokens_used
            )
            
            await db.commit()
            
            return {
                "message": assistant_content,
                "tokens_used": tokens_used,
                "tool_calls": response_message.tool_calls is not None
            }
        
        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            await db.rollback()
            raise
    
    def _build_messages_for_api(self, history: List[Message]) -> List[Dict[str, str]]:
        """
        Build messages list for OpenAI API from chat history
        
        Note: Messages with role 'tool' are excluded because:
        1. OpenAI requires tool messages to have tool_call_id linking to assistant message
        2. Tool results are already included in assistant responses
        3. Tool messages are stored for display purposes only
        """
        messages = []
        
        for msg in history:
            # Skip tool messages - they're not needed for OpenAI API context
            # Tool results are already included in assistant responses
            if msg.role == MessageRole.TOOL:
                continue
            
            messages.append({
                "role": msg.role.value,
                "content": msg.content
            })
        
        return messages
    
    def _tool_to_openai_format(self, tool: Any) -> Dict[str, Any]:
        """Convert LangChain tool to OpenAI function format"""
        # Get parameters schema
        params_schema = {}
        
        if hasattr(tool, "args") and tool.args is not None:
            params_schema = tool.args
        elif hasattr(tool, "args_schema") and tool.args_schema is not None:
            # Try to get JSON schema if available
            schema = tool.args_schema
            if hasattr(schema, "schema"):
                params_schema = schema.schema()
            elif hasattr(schema, "model_json_schema"):
                params_schema = schema.model_json_schema()
            else:
                params_schema = {}
        
        # Ensure parameters is a valid JSON Schema object
        # OpenAI requires type: "object" at the root level with "properties" field
        if not params_schema or not isinstance(params_schema, dict):
            params_schema = {"type": "object", "properties": {}}
        elif "type" not in params_schema:
            # If type is missing, add it with properties
            if "properties" not in params_schema:
                params_schema["properties"] = {}
            params_schema = {"type": "object", **params_schema}
        elif params_schema.get("type") == "object":
            # Ensure properties field exists for object type
            if "properties" not in params_schema:
                params_schema["properties"] = {}
        elif params_schema.get("type") != "object":
            # If type is not "object", wrap it properly
            params_schema = {"type": "object", "properties": params_schema}
        
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": params_schema
            }
        }
    
    def _format_mcp_result(self, tool_result: Any) -> str:
        """
        Extract text content from MCP tool result
        
        Args:
            tool_result: Result from MCP tool call
            
        Returns:
            Formatted text string
        """
        # If it's already a string, return as is
        if isinstance(tool_result, str):
            return tool_result
        
        # If it's a dict, try to extract text content
        if isinstance(tool_result, dict):
            # Try structuredContent first
            if "structuredContent" in tool_result and isinstance(tool_result["structuredContent"], dict):
                if "result" in tool_result["structuredContent"]:
                    return str(tool_result["structuredContent"]["result"])
            
            # Try content field (list of TextContent objects)
            if "content" in tool_result and isinstance(tool_result["content"], list):
                text_parts = []
                for item in tool_result["content"]:
                    if isinstance(item, dict) and "text" in item:
                        text_parts.append(str(item["text"]))
                    elif hasattr(item, "text"):
                        text_parts.append(str(item.text))
                if text_parts:
                    return "\n".join(text_parts)
            
            # If it's a simple dict, try to find text values
            if "result" in tool_result:
                return str(tool_result["result"])
            if "text" in tool_result:
                return str(tool_result["text"])
        
        # If it's an object with attributes, try to extract text
        if hasattr(tool_result, "structuredContent"):
            structured = tool_result.structuredContent
            if isinstance(structured, dict) and "result" in structured:
                return str(structured["result"])
        
        if hasattr(tool_result, "content"):
            content = tool_result.content
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if hasattr(item, "text"):
                        text_parts.append(str(item.text))
                    elif isinstance(item, dict) and "text" in item:
                        text_parts.append(str(item["text"]))
                if text_parts:
                    return "\n".join(text_parts)
        
        # Fallback: convert to string
        return str(tool_result)
    
    def _format_tool_results(self, tool_results: List[Dict[str, Any]]) -> str:
        """Format tool results for display"""
        formatted = ""
        
        for result in tool_results:
            tool_name = result["tool_name"]
            if "error" in result:
                formatted += f"❌ **{tool_name}**: Ошибка - {result['error']}\n\n"
            else:
                # Format the result to extract text content
                formatted_result = self._format_mcp_result(result['result'])
                formatted += f"{formatted_result}\n\n"
        
        return formatted


# Global instance
chat_service = ChatService()

