"""
FastAPI application for Python code execution
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import logging
import os
from dotenv import load_dotenv

from app.executor import executor

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Python Executor Service",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ExecuteRequest(BaseModel):
    """Request model for code execution"""
    code: str
    timeout: Optional[int] = 30


class ExecuteResponse(BaseModel):
    """Response model for code execution"""
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "python-executor"}


@app.post("/execute", response_model=ExecuteResponse)
async def execute_code(request: ExecuteRequest):
    """
    Выполняет Python код в безопасном окружении
    
    Ожидает, что код вернет JSON через print() или установит переменную 'result'
    Формат JSON должен быть:
    {
        "labels": ["Label1", "Label2"],
        "datasets": [{
            "label": "Dataset 1",
            "data": [10, 20],
            "backgroundColor": "#3b82f6"
        }]
    }
    """
    try:
        if not request.code or not request.code.strip():
            raise HTTPException(status_code=400, detail="Code is required")
        
        # Выполнение кода
        result = executor.execute(request.code)
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Code execution failed")
            )
        
        # Валидация формата данных
        data = result["data"]
        if not isinstance(data, dict):
            raise HTTPException(
                status_code=400,
                detail="Result must be a dictionary"
            )
        
        # Проверка наличия обязательных полей
        if "labels" not in data or "datasets" not in data:
            raise HTTPException(
                status_code=400,
                detail="Result must contain 'labels' and 'datasets' fields"
            )
        
        return ExecuteResponse(
            success=True,
            data=data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in execute_code: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8002"))
    uvicorn.run(app, host="0.0.0.0", port=port)

