"""
MCP Server and Tool configuration models
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class MCPTransport(str, enum.Enum):
    """MCP transport protocol enum"""
    STREAMABLE_HTTP = "streamable_http"
    STDIO = "stdio"
    SSE = "sse"


class MCPServer(Base):
    """MCP Server configuration model"""
    __tablename__ = "mcp_servers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    url = Column(String(500), nullable=False)
    transport = Column(Enum(MCPTransport), nullable=False, default=MCPTransport.STREAMABLE_HTTP)
    auth_token = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    tools = relationship("MCPTool", back_populates="server", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<MCPServer(id={self.id}, name='{self.name}', is_active={self.is_active})>"


class MCPTool(Base):
    """MCP Tool configuration model"""
    __tablename__ = "mcp_tools"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("mcp_servers.id", ondelete="CASCADE"), nullable=False)
    tool_name = Column(String(255), nullable=False)
    tool_description = Column(Text, nullable=True)
    custom_name = Column(String(255), nullable=True)
    custom_description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_popular = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    server = relationship("MCPServer", back_populates="tools")

    def __repr__(self):
        return f"<MCPTool(id={self.id}, tool_name='{self.tool_name}', is_active={self.is_active}, is_popular={self.is_popular})>"

