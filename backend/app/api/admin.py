"""
Admin API endpoints
"""
import logging
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


class MCPToolResponse(BaseModel):
    id: int
    server_id: int
    tool_name: str
    tool_description: Optional[str]
    custom_name: Optional[str]
    custom_description: Optional[str]
    is_active: bool
    is_popular: bool
    
    class Config:
        from_attributes = True


@router.get("/mcp/tools", response_model=List[MCPToolResponse])
async def get_mcp_tools(current_admin: CurrentAdminUser, db: DBSession):
    """
    Get all MCP tools (admin only)
    """
    result = await db.execute(select(MCPTool))
    tools = result.scalars().all()
    return tools


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
    result = await db.execute(select(MCPTool).where(MCPTool.id == tool_id))
    tool = result.scalar_one_or_none()
    
    if not tool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
    
    if tool_data.is_active is not None:
        tool.is_active = tool_data.is_active
    if tool_data.is_popular is not None:
        tool.is_popular = tool_data.is_popular
    if tool_data.custom_name is not None:
        tool.custom_name = tool_data.custom_name.strip() if tool_data.custom_name else None
    if tool_data.custom_description is not None:
        tool.custom_description = tool_data.custom_description.strip() if tool_data.custom_description else None
    
    await db.commit()
    await db.refresh(tool)
    
    return tool


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

