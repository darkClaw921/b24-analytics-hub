"""
MCP Service for managing connections to MCP servers
"""
from typing import Dict, List, Any, Optional
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import BaseTool
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.config import settings
from app.models import MCPServer, MCPTransport, MCPTool

logger = logging.getLogger(__name__)


class MCPService:
    """Service for managing MCP server connections and tools"""
    
    def __init__(self):
        self._client: Optional[MultiServerMCPClient] = None
        self._tools_cache: Dict[str, List[BaseTool]] = {}
        self._initialized = False
    
    async def initialize(self, db: Optional[AsyncSession] = None, servers: List[MCPServer] = None):
        """
        Initialize MCP client with configured servers
        
        Args:
            db: Database session to load servers from DB
            servers: Optional list of servers (if None, loads from DB or settings)
        """
        # Build connections config
        connections = {}
        
        # Load servers from database if db session provided
        if db and servers is None:
            result = await db.execute(select(MCPServer).where(MCPServer.is_active == True))
            servers = result.scalars().all()
        
        if servers:
            # Add servers from database
            for server in servers:
                if not server.is_active:
                    continue
                
                # Clean URL: strip whitespace and ensure no trailing spaces
                cleaned_url = server.url.strip() if server.url else ""
                if not cleaned_url:
                    logger.warning(f"Server {server.name} has empty URL, skipping")
                    continue
                    
                server_config = {
                    "url": cleaned_url,
                    "transport": server.transport.value,
                }
                
                if server.auth_token:
                    server_config["headers"] = {
                        "Authorization": f"Bearer {server.auth_token}"
                    }
                
                connections[server.name] = server_config
        else:
            # Fallback: Add Bitrix24 server from settings
            if settings.MCP_BITRIX24_URL:
                connections[settings.MCP_BITRIX24_NAME] = {
                    "url": settings.MCP_BITRIX24_URL,
                    "transport": settings.MCP_BITRIX24_TRANSPORT,
                }
                if settings.MCP_BITRIX24_AUTH_TOKEN:
                    connections[settings.MCP_BITRIX24_NAME]["headers"] = {
                        "Authorization": f"Bearer {settings.MCP_BITRIX24_AUTH_TOKEN}"
                    }
        
        if not connections:
            logger.warning("No active MCP servers configured")
            self._initialized = False
            return
        
        # Initialize client
        self._client = MultiServerMCPClient(connections)
        self._initialized = True
        # Clear cache when reinitializing
        self._tools_cache = {}
        logger.info(f"MCP client initialized with servers: {list(connections.keys())}")
    
    async def get_tools(self, server_name: Optional[str] = None) -> List[BaseTool]:
        """
        Get tools from MCP servers
        
        Args:
            server_name: Optional server name to get tools from specific server
        
        Returns:
            List of LangChain tools
        """
        if not self._initialized:
            await self.initialize()
        
        if not self._client:
            logger.error("MCP client not initialized")
            return []
        
        try:
            # Check cache
            cache_key = server_name or "all"
            if cache_key in self._tools_cache:
                return self._tools_cache[cache_key]
            
            # Get tools from MCP client
            tools = await self._client.get_tools(server_name=server_name)
            
            # Cache tools
            self._tools_cache[cache_key] = tools
            logger.info(f"Loaded {len(tools)} tools from MCP server(s)")
            
            return tools
        except Exception as e:
            logger.error(f"Error getting tools from MCP: {e}")
            return []
    
    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """
        Call a tool directly (bypass LLM)
        
        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool to call
            arguments: Tool arguments
        
        Returns:
            Tool execution result
        """
        if not self._initialized:
            await self.initialize()
        
        if not self._client:
            raise Exception("MCP client not initialized")
        
        try:
            # Create session and call tool
            async with self._client.session(server_name) as session:
                result = await session.call_tool(tool_name, arguments)
                return result
        except Exception as e:
            logger.error(f"Error calling tool {tool_name} on server {server_name}: {e}")
            raise
    
    async def get_tool_metadata(self, server_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get metadata about available tools
        
        Returns:
            List of tool metadata dicts with name, description, parameters
        """
        tools = await self.get_tools(server_name)
        
        metadata = []
        for tool in tools:
            # Get parameters schema
            params_schema = {}
            if hasattr(tool, "args"):
                params_schema = tool.args
            elif hasattr(tool, "args_schema"):
                # Try to get JSON schema if available
                schema = tool.args_schema
                if hasattr(schema, "schema"):
                    params_schema = schema.schema()
                elif hasattr(schema, "model_json_schema"):
                    params_schema = schema.model_json_schema()
                else:
                    params_schema = {}
            
            metadata.append({
                "name": tool.name,
                "description": tool.description or "",
                "parameters": params_schema
            })
        
        return metadata
    
    def clear_cache(self):
        """Clear tools cache"""
        self._tools_cache = {}
        logger.info("MCP tools cache cleared")
    
    async def sync_tools_from_server(self, db: AsyncSession, server: MCPServer):
        """
        Synchronize tools from MCP server to database
        
        Args:
            db: Database session
            server: MCP server to sync tools from
        """
        if not server.is_active:
            logger.info(f"Server {server.name} is not active, skipping sync")
            return
        
        try:
            # Ensure client is initialized with current servers
            if not self._initialized:
                await self.initialize(db=db)
            
            if not self._client:
                logger.error("MCP client not initialized")
                return
            
            # Clear cache to force reload
            if server.name in self._tools_cache:
                del self._tools_cache[server.name]
            if "all" in self._tools_cache:
                del self._tools_cache["all"]
            
            # Get tools from this specific server
            tools = await self.get_tools(server_name=server.name)
            
            if not tools:
                logger.warning(f"No tools found for server {server.name}")
                return
            
            # Get existing tools for this server
            result = await db.execute(
                select(MCPTool).where(MCPTool.server_id == server.id)
            )
            existing_tools = {tool.tool_name: tool for tool in result.scalars().all()}
            
            # Sync tools
            synced_count = 0
            for tool in tools:
                tool_name = tool.name
                tool_description = tool.description if hasattr(tool, "description") else None
                
                if tool_name in existing_tools:
                    # Update existing tool
                    existing_tool = existing_tools[tool_name]
                    existing_tool.tool_description = tool_description
                    synced_count += 1
                else:
                    # Create new tool
                    new_tool = MCPTool(
                        server_id=server.id,
                        tool_name=tool_name,
                        tool_description=tool_description,
                        is_active=True,
                        is_popular=False
                    )
                    db.add(new_tool)
                    synced_count += 1
            
            await db.commit()
            logger.info(f"Synced {synced_count} tools from server {server.name}")
            
        except Exception as e:
            logger.error(f"Error syncing tools from server {server.name}: {e}")
            await db.rollback()
            raise


# Global instance
mcp_service = MCPService()

