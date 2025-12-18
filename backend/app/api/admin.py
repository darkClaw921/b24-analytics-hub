"""
Admin API endpoints
"""
import logging
import json
from urllib.parse import urlparse
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, field_validator
from typing import List, Optional
from sqlalchemy import select

logger = logging.getLogger(__name__)

from app.dependencies import CurrentAdminUser, DBSession
from app.services.user_service import UserService
from app.services.mcp_service import mcp_service
from app.models import MCPServer, MCPTool, MCPTransport, User

router = APIRouter(prefix="/api/admin", tags=["admin"])


# User management
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    is_admin: bool = False


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool
    
    class Config:
        from_attributes = True


@router.get("/users", response_model=List[UserResponse])
async def get_users(current_admin: CurrentAdminUser, db: DBSession):
    """
    Get all users (admin only)
    """
    users = await UserService.get_all_users(db)
    return users


@router.post("/users", response_model=UserResponse)
async def create_user(user_data: UserCreate, current_admin: CurrentAdminUser, db: DBSession):
    """
    Create a new user (admin only)
    """
    # Check if username or email already exists
    existing_user = await UserService.get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    existing_email = await UserService.get_user_by_email(db, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    user = await UserService.create_user(
        db,
        user_data.username,
        user_data.email,
        user_data.password,
        user_data.is_admin
    )
    
    await db.commit()
    
    return user


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, current_admin: CurrentAdminUser, db: DBSession):
    """
    Delete user (admin only)
    """
    # Prevent deleting self
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    success = await UserService.delete_user(db, user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await db.commit()
    
    return {"message": "User deleted successfully"}


# MCP Server management
class MCPServerCreate(BaseModel):
    name: str
    url: str
    transport: MCPTransport
    auth_token: Optional[str] = None
    is_active: bool = True
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate and clean URL"""
        if not v:
            raise ValueError("URL cannot be empty")
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("URL cannot be empty")
        # Basic URL validation
        try:
            parsed = urlparse(cleaned)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid URL format")
        except Exception:
            raise ValueError("Invalid URL format")
        return cleaned
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Clean name"""
        return v.strip()
    
    @field_validator('auth_token')
    @classmethod
    def validate_auth_token(cls, v: Optional[str]) -> Optional[str]:
        """Clean auth token"""
        return v.strip() if v else None


class MCPServerUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    transport: Optional[MCPTransport] = None
    auth_token: Optional[str] = None
    is_active: Optional[bool] = None
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean URL"""
        if v is None:
            return None
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("URL cannot be empty")
        # Basic URL validation
        try:
            parsed = urlparse(cleaned)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid URL format")
        except Exception:
            raise ValueError("Invalid URL format")
        return cleaned
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Clean name"""
        return v.strip() if v else None
    
    @field_validator('auth_token')
    @classmethod
    def validate_auth_token(cls, v: Optional[str]) -> Optional[str]:
        """Clean auth token"""
        return v.strip() if v else None


class MCPServerResponse(BaseModel):
    id: int
    name: str
    url: str
    transport: MCPTransport
    is_active: bool
    
    class Config:
        from_attributes = True


@router.get("/mcp/servers", response_model=List[MCPServerResponse])
async def get_mcp_servers(current_admin: CurrentAdminUser, db: DBSession):
    """
    Get all MCP servers (admin only)
    """
    result = await db.execute(select(MCPServer))
    servers = result.scalars().all()
    return servers


@router.post("/mcp/servers", response_model=MCPServerResponse)
async def create_mcp_server(
    server_data: MCPServerCreate,
    current_admin: CurrentAdminUser,
    db: DBSession
):
    """
    Create a new MCP server (admin only)
    """
    # Check if name already exists
    result = await db.execute(select(MCPServer).where(MCPServer.name == server_data.name))
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Server name already exists"
        )
    
    # URL and name are already cleaned by validators
    server = MCPServer(
        name=server_data.name,
        url=server_data.url,
        transport=server_data.transport,
        auth_token=server_data.auth_token,
        is_active=server_data.is_active
    )
    
    db.add(server)
    await db.flush()
    await db.refresh(server)
    await db.commit()
    
    # Sync tools from the new server if it's active
    if server.is_active:
        try:
            await mcp_service.sync_tools_from_server(db, server)
        except Exception as e:
            logger.error(f"Error syncing tools after server creation: {e}")
            # Don't fail the request, just log the error
    
    return server


@router.put("/mcp/servers/{server_id}", response_model=MCPServerResponse)
async def update_mcp_server(
    server_id: int,
    server_data: MCPServerUpdate,
    current_admin: CurrentAdminUser,
    db: DBSession
):
    """
    Update MCP server (admin only)
    """
    result = await db.execute(select(MCPServer).where(MCPServer.id == server_id))
    server = result.scalar_one_or_none()
    
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
    
    # Update fields (already cleaned by validators)
    if server_data.name is not None:
        server.name = server_data.name
    if server_data.url is not None:
        server.url = server_data.url
    if server_data.transport is not None:
        server.transport = server_data.transport
    if server_data.auth_token is not None:
        server.auth_token = server_data.auth_token
    if server_data.is_active is not None:
        server.is_active = server_data.is_active
    
    await db.commit()
    await db.refresh(server)
    
    # Reinitialize MCP client and sync tools if server is active
    if server.is_active:
        try:
            await mcp_service.initialize(db=db)
            await mcp_service.sync_tools_from_server(db, server)
        except Exception as e:
            logger.error(f"Error syncing tools after server update: {e}")
            # Don't fail the request, just log the error
    
    return server


@router.delete("/mcp/servers/{server_id}")
async def delete_mcp_server(
    server_id: int,
    current_admin: CurrentAdminUser,
    db: DBSession
):
    """
    Delete MCP server (admin only)
    """
    result = await db.execute(select(MCPServer).where(MCPServer.id == server_id))
    server = result.scalar_one_or_none()
    
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
    
    await db.delete(server)
    await db.commit()
    
    return {"message": "Server deleted successfully"}


# MCP Tool management
class MCPToolUpdate(BaseModel):
    is_active: Optional[bool] = None
    is_popular: Optional[bool] = None
    custom_name: Optional[str] = None
    custom_description: Optional[str] = None
    parameter_display_names: Optional[dict] = None  # {"original_param": "display_name"}
    hidden_parameters: Optional[list] = None  # ["param1", "param2"] - список скрытых параметров


class MCPToolResponse(BaseModel):
    id: int
    server_id: int
    tool_name: str
    tool_description: Optional[str]
    custom_name: Optional[str]
    custom_description: Optional[str]
    parameter_display_names: Optional[dict] = None
    hidden_parameters: Optional[list] = None
    is_active: bool
    is_popular: bool
    
    class Config:
        from_attributes = True


@router.get("/mcp/tools", response_model=List[MCPToolResponse])
async def get_mcp_tools(current_admin: CurrentAdminUser, db: DBSession):
    """
    Get all MCP tools (admin only)
    """
    # Check if parameter_display_names column exists
    try:
        # Try to query with the column - if it fails, column doesn't exist
        result = await db.execute(select(MCPTool))
        tools = result.scalars().all()
    except Exception as e:
        if "no such column" in str(e).lower() or "parameter_display_names" in str(e):
            # Column doesn't exist yet - use raw SQL to select without it
            logger.warning("parameter_display_names column not found, using fallback query")
            from sqlalchemy import text
            result = await db.execute(text("""
                SELECT id, server_id, tool_name, tool_description, 
                       custom_name, custom_description, is_active, is_popular, created_at
                FROM mcp_tools
            """))
            rows = result.all()
            # Create MCPTool instances manually
            tools = []
            for row in rows:
                # Create a simple object with the attributes
                class ToolProxy:
                    pass
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
                tools.append(tool)
        else:
            raise
    
    # Convert parameter_display_names and hidden_parameters from JSON string to dict/list
    tools_list = []
    for tool in tools:
        # Use getattr in case migration not applied or tool is a proxy object
        param_display_names = getattr(tool, 'parameter_display_names', None)
        param_display_names_dict = None
        if param_display_names:
            try:
                param_display_names_dict = json.loads(param_display_names)
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Error parsing parameter_display_names for tool {getattr(tool, 'tool_name', 'unknown')}: {e}")
                param_display_names_dict = None
        
        hidden_params = getattr(tool, 'hidden_parameters', None)
        hidden_params_list = None
        if hidden_params:
            try:
                hidden_params_list = json.loads(hidden_params)
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Error parsing hidden_parameters for tool {getattr(tool, 'tool_name', 'unknown')}: {e}")
                hidden_params_list = None
        
        tool_dict = {
            "id": tool.id,
            "server_id": tool.server_id,
            "tool_name": tool.tool_name,
            "tool_description": tool.tool_description,
            "custom_name": tool.custom_name,
            "custom_description": tool.custom_description,
            "parameter_display_names": param_display_names_dict,
            "hidden_parameters": hidden_params_list,
            "is_active": tool.is_active,
            "is_popular": tool.is_popular,
        }
        tools_list.append(tool_dict)
    
    return tools_list


@router.get("/mcp/tools/{tool_id}/parameters")
async def get_tool_parameters(
    tool_id: int,
    current_admin: CurrentAdminUser,
    db: DBSession
):
    """
    Get tool parameters schema from MCP service (admin only)
    """
    # Check if parameter_display_names column exists
    try:
        result = await db.execute(select(MCPTool).where(MCPTool.id == tool_id))
        tool = result.scalar_one_or_none()
    except Exception as e:
        if "no such column" in str(e).lower() or "parameter_display_names" in str(e):
            # Column doesn't exist yet - use raw SQL to select without it
            logger.warning("parameter_display_names column not found, using fallback query")
            from sqlalchemy import text
            result = await db.execute(text("""
                SELECT id, server_id, tool_name, tool_description, 
                       custom_name, custom_description, is_active, is_popular, created_at
                FROM mcp_tools
                WHERE id = :tool_id
            """), {"tool_id": tool_id})
            row = result.first()
            if not row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
            
            # Create a simple object with the attributes
            class ToolProxy:
                pass
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
        else:
            raise
    
    if not tool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
    
    # Get server
    server_result = await db.execute(select(MCPServer).where(MCPServer.id == tool.server_id))
    server = server_result.scalar_one_or_none()
    
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
    
    # Get tool metadata from MCP service
    try:
        all_metadata = await mcp_service.get_tool_metadata(server.name)
        tool_metadata = next((t for t in all_metadata if t["name"] == tool.tool_name), None)
        
        if not tool_metadata:
            logger.warning(f"Tool metadata not found for tool_id={tool_id}, tool_name={tool.tool_name}")
            return {"parameters": {}}
        
        params = tool_metadata.get("parameters", {})
        logger.debug(f"Found parameters for tool {tool.tool_name}: {params}")
        return {"parameters": params}
    except Exception as e:
        logger.error(f"Error getting tool parameters for tool_id={tool_id}: {e}", exc_info=True)
        return {"parameters": {}}


@router.put("/mcp/tools/{tool_id}", response_model=MCPToolResponse)
async def update_mcp_tool(
    tool_id: int,
    tool_data: MCPToolUpdate,
    current_admin: CurrentAdminUser,
    db: DBSession
):
    """
    Update MCP tool settings (admin only)
    """
    import sqlite3
    from sqlalchemy import text
    
    try:
        result = await db.execute(select(MCPTool).where(MCPTool.id == tool_id))
        tool = result.scalar_one_or_none()
        use_orm = True
    except (sqlite3.OperationalError, Exception) as e:
        # Fallback if column doesn't exist (migration not applied)
        if 'parameter_display_names' in str(e) or 'no such column' in str(e).lower():
            logger.warning(f"Migration may not be applied, using fallback query for tool {tool_id}")
            use_orm = False
            # Use raw SQL to select without parameter_display_names and hidden_parameters
            # Try to select with hidden_parameters first, fallback if column doesn't exist
            try:
                result = await db.execute(
                    text("""
                        SELECT id, server_id, tool_name, tool_description, custom_name, 
                               custom_description, is_active, is_popular, created_at, hidden_parameters
                        FROM mcp_tools WHERE id = :tool_id
                    """),
                    {"tool_id": tool_id}
                )
                has_hidden_params_col = True
            except Exception:
                # Column doesn't exist yet, select without it
                result = await db.execute(
                    text("""
                        SELECT id, server_id, tool_name, tool_description, custom_name, 
                               custom_description, is_active, is_popular, created_at
                        FROM mcp_tools WHERE id = :tool_id
                    """),
                    {"tool_id": tool_id}
                )
                has_hidden_params_col = False
            row = result.fetchone()
            if not row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
            tool = None  # Will use raw SQL for updates
        else:
            raise
    
    if use_orm:
        if not tool:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
        
        # Normal ORM update
        if tool_data.is_active is not None:
            tool.is_active = tool_data.is_active
        if tool_data.is_popular is not None:
            tool.is_popular = tool_data.is_popular
        if tool_data.custom_name is not None:
            tool.custom_name = tool_data.custom_name.strip() if tool_data.custom_name else None
        if tool_data.custom_description is not None:
            tool.custom_description = tool_data.custom_description.strip() if tool_data.custom_description else None
        if tool_data.parameter_display_names is not None:
            # Store as JSON string (use setattr in case migration not applied)
            if hasattr(tool, 'parameter_display_names'):
                tool.parameter_display_names = json.dumps(tool_data.parameter_display_names) if tool_data.parameter_display_names else None
            else:
                logger.warning(f"Field parameter_display_names not found for tool {tool.id}, migration may not be applied")
        
        if tool_data.hidden_parameters is not None:
            # Store as JSON string (use setattr in case migration not applied)
            if hasattr(tool, 'hidden_parameters'):
                tool.hidden_parameters = json.dumps(tool_data.hidden_parameters) if tool_data.hidden_parameters else None
            else:
                logger.warning(f"Field hidden_parameters not found for tool {tool.id}, migration may not be applied")
        
        await db.commit()
        await db.refresh(tool)
        
        # Build response
        param_display_names = getattr(tool, 'parameter_display_names', None)
        param_display_names_dict = None
        if param_display_names:
            try:
                param_display_names_dict = json.loads(param_display_names)
            except (json.JSONDecodeError, TypeError):
                param_display_names_dict = None
        
        hidden_params = getattr(tool, 'hidden_parameters', None)
        hidden_params_list = None
        if hidden_params:
            try:
                hidden_params_list = json.loads(hidden_params)
            except (json.JSONDecodeError, TypeError):
                hidden_params_list = None
        
        return {
            "id": tool.id,
            "server_id": tool.server_id,
            "tool_name": tool.tool_name,
            "tool_description": tool.tool_description,
            "custom_name": tool.custom_name,
            "custom_description": tool.custom_description,
            "parameter_display_names": param_display_names_dict,
            "hidden_parameters": hidden_params_list,
            "is_active": tool.is_active,
            "is_popular": tool.is_popular,
        }
    else:
        # Use raw SQL for updates (migration not applied)
        # Check if hidden_parameters column exists by trying to select it
        has_hidden_params_col = False
        try:
            test_result = await db.execute(
                text("SELECT hidden_parameters FROM mcp_tools LIMIT 1")
            )
            test_result.fetchone()
            has_hidden_params_col = True
        except Exception:
            has_hidden_params_col = False
        
        updates = []
        params = {"tool_id": tool_id}
        
        if tool_data.is_active is not None:
            updates.append("is_active = :is_active")
            params["is_active"] = tool_data.is_active
        if tool_data.is_popular is not None:
            updates.append("is_popular = :is_popular")
            params["is_popular"] = tool_data.is_popular
        if tool_data.custom_name is not None:
            updates.append("custom_name = :custom_name")
            params["custom_name"] = tool_data.custom_name.strip() if tool_data.custom_name else None
        if tool_data.custom_description is not None:
            updates.append("custom_description = :custom_description")
            params["custom_description"] = tool_data.custom_description.strip() if tool_data.custom_description else None
        if tool_data.hidden_parameters is not None and has_hidden_params_col:
            updates.append("hidden_parameters = :hidden_parameters")
            params["hidden_parameters"] = json.dumps(tool_data.hidden_parameters) if tool_data.hidden_parameters else None
        
        if updates:
            await db.execute(
                text(f"UPDATE mcp_tools SET {', '.join(updates)} WHERE id = :tool_id"),
                params
            )
            await db.commit()
        
        # Re-fetch the tool
        if has_hidden_params_col:
            result = await db.execute(
                text("""
                    SELECT id, server_id, tool_name, tool_description, custom_name, 
                           custom_description, is_active, is_popular, created_at, hidden_parameters
                    FROM mcp_tools WHERE id = :tool_id
                """),
                {"tool_id": tool_id}
            )
        else:
            result = await db.execute(
                text("""
                    SELECT id, server_id, tool_name, tool_description, custom_name, 
                           custom_description, is_active, is_popular, created_at
                    FROM mcp_tools WHERE id = :tool_id
                """),
                {"tool_id": tool_id}
            )
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
        
        # Check if hidden_parameters was included in the query
        hidden_params = None
        if has_hidden_params_col and len(row) > 9:  # hidden_parameters column exists
            hidden_params_raw = row[9]
            if hidden_params_raw:
                try:
                    hidden_params = json.loads(hidden_params_raw)
                except (json.JSONDecodeError, TypeError):
                    hidden_params = None
        
        return {
            "id": row[0],
            "server_id": row[1],
            "tool_name": row[2],
            "tool_description": row[3],
            "custom_name": row[4],
            "custom_description": row[5],
            "parameter_display_names": None,  # Column doesn't exist yet
            "hidden_parameters": hidden_params,
            "is_active": bool(row[6]),
            "is_popular": bool(row[7]),
        }


@router.post("/mcp/servers/{server_id}/sync-tools")
async def sync_server_tools(
    server_id: int,
    current_admin: CurrentAdminUser,
    db: DBSession
):
    """
    Manually sync tools from MCP server (admin only)
    """
    result = await db.execute(select(MCPServer).where(MCPServer.id == server_id))
    server = result.scalar_one_or_none()
    
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
    
    # Clean URL if it has whitespace
    if server.url != server.url.strip():
        server.url = server.url.strip()
        await db.commit()
        await db.refresh(server)
        logger.info(f"Cleaned URL for server {server.name}")
    
    try:
        await mcp_service.sync_tools_from_server(db, server)
        return {"message": f"Tools synced successfully from server {server.name}"}
    except Exception as e:
        logger.error(f"Error syncing tools: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error syncing tools: {str(e)}"
        )

