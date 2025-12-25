"""
Dashboards API endpoints
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.dependencies import CurrentUser, DBSession
from app.models import Dashboard, Chart, ChartType
from app.services.dashboard_service import dashboard_service

router = APIRouter(prefix="/api/dashboards", tags=["dashboards"])


# Pydantic schemas
class DashboardCreate(BaseModel):
    title: str
    description: Optional[str] = None


class DashboardUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class ChartResponse(BaseModel):
    id: int
    dashboard_id: int
    title: str
    chart_type: str
    position_x: int
    position_y: int
    width: int
    height: int
    python_code: str
    config: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DashboardResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    charts: List[ChartResponse] = []
    
    class Config:
        from_attributes = True


class DashboardListItem(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ChartCreate(BaseModel):
    title: str
    chart_type: str
    python_code: str
    position_x: int = 0
    position_y: int = 0
    width: int = 400
    height: int = 300
    config: Optional[Dict[str, Any]] = None


class ChartUpdate(BaseModel):
    title: Optional[str] = None
    chart_type: Optional[str] = None
    python_code: Optional[str] = None
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    config: Optional[Dict[str, Any]] = None


class ChartExecuteResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# Dashboard endpoints
@router.get("", response_model=List[DashboardListItem])
async def get_dashboards(current_user: CurrentUser, db: DBSession):
    """
    Get all dashboards for current user
    """
    dashboards = await dashboard_service.get_user_dashboards(db, current_user.id)
    return dashboards


@router.post("", response_model=DashboardResponse)
async def create_dashboard(
    dashboard_data: DashboardCreate,
    current_user: CurrentUser,
    db: DBSession
):
    """
    Create a new dashboard
    """
    dashboard = await dashboard_service.create_dashboard(
        db=db,
        user_id=current_user.id,
        title=dashboard_data.title,
        description=dashboard_data.description
    )
    
    await db.commit()
    
    # Load charts
    await db.refresh(dashboard, ["charts"])
    
    return dashboard


@router.get("/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    dashboard_id: int,
    current_user: CurrentUser,
    db: DBSession
):
    """
    Get dashboard by ID with charts
    """
    dashboard = await dashboard_service.get_dashboard(db, dashboard_id, current_user.id)
    
    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found"
        )
    
    # Load charts
    await db.refresh(dashboard, ["charts"])
    
    return dashboard


@router.put("/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: int,
    dashboard_data: DashboardUpdate,
    current_user: CurrentUser,
    db: DBSession
):
    """
    Update dashboard
    """
    dashboard = await dashboard_service.update_dashboard(
        db=db,
        dashboard_id=dashboard_id,
        user_id=current_user.id,
        title=dashboard_data.title,
        description=dashboard_data.description
    )
    
    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found"
        )
    
    await db.commit()
    await db.refresh(dashboard, ["charts"])
    
    return dashboard


@router.delete("/{dashboard_id}")
async def delete_dashboard(
    dashboard_id: int,
    current_user: CurrentUser,
    db: DBSession
):
    """
    Delete dashboard
    """
    deleted = await dashboard_service.delete_dashboard(
        db=db,
        dashboard_id=dashboard_id,
        user_id=current_user.id
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found"
        )
    
    await db.commit()
    
    return {"message": "Dashboard deleted successfully"}


# Chart endpoints
@router.post("/{dashboard_id}/charts", response_model=ChartResponse)
async def create_chart(
    dashboard_id: int,
    chart_data: ChartCreate,
    current_user: CurrentUser,
    db: DBSession
):
    """
    Create a new chart in dashboard
    """
    # Verify dashboard belongs to user
    dashboard = await dashboard_service.get_dashboard(db, dashboard_id, current_user.id)
    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found"
        )
    
    # Validate chart_type
    try:
        chart_type = ChartType(chart_data.chart_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid chart_type. Must be one of: {[t.value for t in ChartType]}"
        )
    
    chart = await dashboard_service.create_chart(
        db=db,
        dashboard_id=dashboard_id,
        title=chart_data.title,
        chart_type=chart_type,
        python_code=chart_data.python_code,
        position_x=chart_data.position_x,
        position_y=chart_data.position_y,
        width=chart_data.width,
        height=chart_data.height,
        config=chart_data.config
    )
    
    await db.commit()
    await db.refresh(chart)
    
    return chart


@router.put("/charts/{chart_id}", response_model=ChartResponse)
async def update_chart(
    chart_id: int,
    chart_data: ChartUpdate,
    current_user: CurrentUser,
    db: DBSession
):
    """
    Update chart
    """
    chart_type = None
    if chart_data.chart_type:
        try:
            chart_type = ChartType(chart_data.chart_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid chart_type. Must be one of: {[t.value for t in ChartType]}"
            )
    
    chart = await dashboard_service.update_chart(
        db=db,
        chart_id=chart_id,
        user_id=current_user.id,
        title=chart_data.title,
        chart_type=chart_type,
        python_code=chart_data.python_code,
        position_x=chart_data.position_x,
        position_y=chart_data.position_y,
        width=chart_data.width,
        height=chart_data.height,
        config=chart_data.config
    )
    
    if not chart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chart not found"
        )
    
    await db.commit()
    await db.refresh(chart)
    
    return chart


@router.delete("/charts/{chart_id}")
async def delete_chart(
    chart_id: int,
    current_user: CurrentUser,
    db: DBSession
):
    """
    Delete chart
    """
    deleted = await dashboard_service.delete_chart(
        db=db,
        chart_id=chart_id,
        user_id=current_user.id
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chart not found"
        )
    
    await db.commit()
    
    return {"message": "Chart deleted successfully"}


@router.post("/charts/{chart_id}/execute", response_model=ChartExecuteResponse)
async def execute_chart(
    chart_id: int,
    current_user: CurrentUser,
    db: DBSession
):
    """
    Execute Python code for chart and return data
    """
    result = await dashboard_service.execute_chart_code(
        db=db,
        chart_id=chart_id,
        user_id=current_user.id
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Chart execution failed")
        )
    
    return ChartExecuteResponse(
        success=True,
        data=result.get("data")
    )

