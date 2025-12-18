"""
MCP API endpoints
"""
import json
import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from sqlalchemy import select

from app.dependencies import CurrentUser, DBSession
from app.services.mcp_service import mcp_service
from app.models import MCPTool, MCPServer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mcp", tags=["mcp"])


class ToolCallRequest(BaseModel):
    server_name: str
    tool_name: str
    arguments: Dict[str, Any]


class ToolMetadata(BaseModel):
    name: str  # Реальное имя инструмента (используется для вызова)
    description: str  # Реальное описание инструмента
    display_name: Optional[str] = None  # Кастомное имя для визуального отображения
    display_description: Optional[str] = None  # Кастомное описание для визуального отображения
    parameters: Dict[str, Any]
    parameter_display_names: Optional[Dict[str, str]] = None  # {"original_param": "display_name"}
    server_name: Optional[str] = None


@router.get("/tools", response_model=List[ToolMetadata])
async def get_tools(current_user: CurrentUser, db: DBSession):
    """
    Get list of popular MCP tools (marked as popular in admin panel)
    """
    try:
        # Get popular tools from database
        try:
            result = await db.execute(
                select(MCPTool).where(MCPTool.is_popular == True, MCPTool.is_active == True)
            )
            popular_tools = result.scalars().all()
        except Exception as e:
            if "no such column" in str(e).lower() or "parameter_display_names" in str(e):
                # Column doesn't exist yet - use raw SQL to select without it
                logger.warning("parameter_display_names column not found, using fallback query")
                from sqlalchemy import text
                result = await db.execute(text("""
                    SELECT id, server_id, tool_name, tool_description, 
                           custom_name, custom_description, is_active, is_popular, created_at
                    FROM mcp_tools
                    WHERE is_popular = 1 AND is_active = 1
                """))
                rows = result.all()
                # Create simple objects with the attributes
                class ToolProxy:
                    pass
                popular_tools = []
                for row in rows:
                    tool = ToolProxy()
                    tool.id = row[0]
                    tool.server_id = row[1]
                    tool.tool_name = row[2]
                    tool.tool_description = row[3]
                    tool.custom_name = row[4]
                    tool.custom_description = row[5]
                    tool.is_active = row[6]
                    tool.is_popular = row[7]
                    tool.created_at = row[8]
                    tool.parameter_display_names = None
                    popular_tools.append(tool)
            else:
                raise
        
        if not popular_tools:
            return []
        
        # Get tool names
        popular_tool_names = {tool.tool_name for tool in popular_tools}
        
        # Get all tool metadata from MCP service
        all_metadata = await mcp_service.get_tool_metadata()
        
        # Create mapping of tool_name to server_name
        tool_to_server = {tool.tool_name: tool.server_id for tool in popular_tools}
        
        # Get server names
        server_result = await db.execute(
            select(MCPServer).where(MCPServer.id.in_(set(tool_to_server.values())))
        )
        servers = {server.id: server.name for server in server_result.scalars().all()}
        
        # Create mapping of tool_name to tool object for custom values
        tool_name_to_db_tool = {tool.tool_name: tool for tool in popular_tools}
        
        # Filter to only popular tools and add server_name, add custom values for display
        popular_metadata = []
        for tool in all_metadata:
            if tool["name"] in popular_tool_names:
                server_id = tool_to_server.get(tool["name"])
                server_name = servers.get(server_id) if server_id else None
                db_tool = tool_name_to_db_tool.get(tool["name"])
                
                tool_with_server = tool.copy()
                tool_with_server["server_name"] = server_name
                
                # Add custom name and description for display (name and description remain original for API calls)
                if db_tool:
                    if db_tool.custom_name:
                        tool_with_server["display_name"] = db_tool.custom_name
                    if db_tool.custom_description:
                        tool_with_server["display_description"] = db_tool.custom_description
                    # Add parameter display names mapping (use getattr in case migration not applied)
                    param_display_names = getattr(db_tool, 'parameter_display_names', None)
                    if param_display_names:
                        try:
                            tool_with_server["parameter_display_names"] = json.loads(param_display_names)
                        except (json.JSONDecodeError, TypeError) as e:
                            logger.warning(f"Error parsing parameter_display_names for tool {tool['name']}: {e}")
                            tool_with_server["parameter_display_names"] = {}
                    else:
                        tool_with_server["parameter_display_names"] = {}
                else:
                    # If db_tool not found, set empty parameter_display_names
                    tool_with_server["parameter_display_names"] = {}
                
                popular_metadata.append(tool_with_server)
        
        return popular_metadata
    except Exception as e:
        logger.error(f"Error getting tools: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting tools: {str(e)}"
        )


@router.post("/call-tool")
async def call_tool(request: ToolCallRequest, current_user: CurrentUser):
    """
    Call MCP tool directly (bypass LLM)
    """
    try:
        result = await mcp_service.call_tool(
            request.server_name,
            request.tool_name,
            request.arguments
        )
        
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calling tool: {str(e)}"
        )

