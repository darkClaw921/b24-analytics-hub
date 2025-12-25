"""
Main FastAPI application
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.config import settings
from app.database import init_db, AsyncSessionLocal
from app.api import auth, users, chats, messages, mcp, admin, dashboards
from app.services.mcp_service import mcp_service

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Disable SQLAlchemy engine logging
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)

# Enable DEBUG for auth modules
if settings.DEBUG:
    logging.getLogger("app.auth").setLevel(logging.DEBUG)
    logging.getLogger("app.dependencies").setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Validate settings
    try:
        settings.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Initialize MCP service with servers from database
    async with AsyncSessionLocal() as db:
        await mcp_service.initialize(db=db)
    logger.info("MCP service initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down application")


# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(chats.router)
app.include_router(messages.router)
app.include_router(mcp.router)
app.include_router(admin.router)
app.include_router(dashboards.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


# WebSocket for real-time chat updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, chat_id: int):
        await websocket.accept()
        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = []
        self.active_connections[chat_id].append(websocket)
        logger.info(f"WebSocket connected to chat {chat_id}")
    
    def disconnect(self, websocket: WebSocket, chat_id: int):
        if chat_id in self.active_connections:
            self.active_connections[chat_id].remove(websocket)
            if not self.active_connections[chat_id]:
                del self.active_connections[chat_id]
        logger.info(f"WebSocket disconnected from chat {chat_id}")
    
    async def broadcast_to_chat(self, chat_id: int, message: dict):
        if chat_id in self.active_connections:
            for connection in self.active_connections[chat_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to WebSocket: {e}")


manager = ConnectionManager()


@app.websocket("/ws/chats/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: int):
    """
    WebSocket endpoint for real-time chat updates
    """
    await manager.connect(websocket, chat_id)
    try:
        while True:
            # Keep connection alive and handle incoming messages if needed
            data = await websocket.receive_text()
            # Echo back for now (in production, handle message processing here)
            await websocket.send_json({
                "type": "ping",
                "message": "pong"
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket, chat_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, chat_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

