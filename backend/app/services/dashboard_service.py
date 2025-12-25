"""
Dashboard service for managing dashboards and charts
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import httpx

from app.config import settings
from app.models import Dashboard, Chart, ChartType

logger = logging.getLogger(__name__)


class DashboardService:
    """Service for managing dashboards and charts"""
    
    def __init__(self):
        self.executor_url = settings.PYTHON_EXECUTOR_URL
        self.executor_timeout = settings.PYTHON_EXECUTOR_TIMEOUT
    
    async def create_dashboard(
        self,
        db: AsyncSession,
        user_id: int,
        title: str,
        description: Optional[str] = None
    ) -> Dashboard:
        """
        Create a new dashboard
        
        Args:
            db: Database session
            user_id: User ID
            title: Dashboard title
            description: Optional description
            
        Returns:
            Created dashboard
        """
        dashboard = Dashboard(
            user_id=user_id,
            title=title,
            description=description
        )
        
        db.add(dashboard)
        await db.flush()
        await db.refresh(dashboard)
        
        return dashboard
    
    async def get_dashboard(
        self,
        db: AsyncSession,
        dashboard_id: int,
        user_id: int
    ) -> Optional[Dashboard]:
        """
        Get dashboard by ID (only if belongs to user)
        
        Args:
            db: Database session
            dashboard_id: Dashboard ID
            user_id: User ID
            
        Returns:
            Dashboard or None
        """
        result = await db.execute(
            select(Dashboard)
            .where(Dashboard.id == dashboard_id, Dashboard.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_dashboards(
        self,
        db: AsyncSession,
        user_id: int
    ) -> List[Dashboard]:
        """
        Get all dashboards for a user
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            List of dashboards
        """
        result = await db.execute(
            select(Dashboard)
            .where(Dashboard.user_id == user_id)
            .order_by(Dashboard.updated_at.desc())
        )
        return result.scalars().all()
    
    async def update_dashboard(
        self,
        db: AsyncSession,
        dashboard_id: int,
        user_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[Dashboard]:
        """
        Update dashboard
        
        Args:
            db: Database session
            dashboard_id: Dashboard ID
            user_id: User ID
            title: Optional new title
            description: Optional new description
            
        Returns:
            Updated dashboard or None
        """
        dashboard = await self.get_dashboard(db, dashboard_id, user_id)
        if not dashboard:
            return None
        
        if title is not None:
            dashboard.title = title
        if description is not None:
            dashboard.description = description
        
        await db.flush()
        await db.refresh(dashboard)
        
        return dashboard
    
    async def delete_dashboard(
        self,
        db: AsyncSession,
        dashboard_id: int,
        user_id: int
    ) -> bool:
        """
        Delete dashboard
        
        Args:
            db: Database session
            dashboard_id: Dashboard ID
            user_id: User ID
            
        Returns:
            True if deleted, False if not found
        """
        dashboard = await self.get_dashboard(db, dashboard_id, user_id)
        if not dashboard:
            return False
        
        await db.delete(dashboard)
        await db.flush()
        
        return True
    
    async def create_chart(
        self,
        db: AsyncSession,
        dashboard_id: int,
        title: str,
        chart_type: ChartType,
        python_code: str,
        position_x: int = 0,
        position_y: int = 0,
        width: int = 400,
        height: int = 300,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[Chart]:
        """
        Create a new chart in dashboard
        
        Args:
            db: Database session
            dashboard_id: Dashboard ID
            title: Chart title
            chart_type: Chart type
            python_code: Python code for generating chart data
            position_x: X position
            position_y: Y position
            width: Chart width
            height: Chart height
            config: Optional chart configuration
            
        Returns:
            Created chart or None if dashboard not found
        """
        # Verify dashboard exists
        result = await db.execute(
            select(Dashboard).where(Dashboard.id == dashboard_id)
        )
        dashboard = result.scalar_one_or_none()
        if not dashboard:
            return None
        
        chart = Chart(
            dashboard_id=dashboard_id,
            title=title,
            chart_type=chart_type,
            python_code=python_code,
            position_x=position_x,
            position_y=position_y,
            width=width,
            height=height,
            config=config
        )
        
        db.add(chart)
        await db.flush()
        await db.refresh(chart)
        
        return chart
    
    async def get_chart(
        self,
        db: AsyncSession,
        chart_id: int,
        user_id: int
    ) -> Optional[Chart]:
        """
        Get chart by ID (only if belongs to user's dashboard)
        
        Args:
            db: Database session
            chart_id: Chart ID
            user_id: User ID
            
        Returns:
            Chart or None
        """
        result = await db.execute(
            select(Chart)
            .join(Dashboard)
            .where(Chart.id == chart_id, Dashboard.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def update_chart(
        self,
        db: AsyncSession,
        chart_id: int,
        user_id: int,
        title: Optional[str] = None,
        chart_type: Optional[ChartType] = None,
        python_code: Optional[str] = None,
        position_x: Optional[int] = None,
        position_y: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[Chart]:
        """
        Update chart
        
        Args:
            db: Database session
            chart_id: Chart ID
            user_id: User ID
            title: Optional new title
            chart_type: Optional new chart type
            python_code: Optional new Python code
            position_x: Optional new X position
            position_y: Optional new Y position
            width: Optional new width
            height: Optional new height
            config: Optional new config
            
        Returns:
            Updated chart or None
        """
        chart = await self.get_chart(db, chart_id, user_id)
        if not chart:
            return None
        
        if title is not None:
            chart.title = title
        if chart_type is not None:
            chart.chart_type = chart_type
        if python_code is not None:
            chart.python_code = python_code
        if position_x is not None:
            chart.position_x = position_x
        if position_y is not None:
            chart.position_y = position_y
        if width is not None:
            chart.width = width
        if height is not None:
            chart.height = height
        if config is not None:
            chart.config = config
        
        await db.flush()
        await db.refresh(chart)
        
        return chart
    
    async def delete_chart(
        self,
        db: AsyncSession,
        chart_id: int,
        user_id: int
    ) -> bool:
        """
        Delete chart
        
        Args:
            db: Database session
            chart_id: Chart ID
            user_id: User ID
            
        Returns:
            True if deleted, False if not found
        """
        chart = await self.get_chart(db, chart_id, user_id)
        if not chart:
            return False
        
        await db.delete(chart)
        await db.flush()
        
        return True
    
    async def execute_chart_code(
        self,
        db: AsyncSession,
        chart_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Execute Python code for chart and return data
        
        Args:
            db: Database session
            chart_id: Chart ID
            user_id: User ID
            
        Returns:
            Dict with chart data or error
        """
        chart = await self.get_chart(db, chart_id, user_id)
        if not chart:
            return {
                "success": False,
                "error": "Chart not found"
            }
        
        try:
            # Вызов Python Executor Service
            async with httpx.AsyncClient(timeout=self.executor_timeout) as client:
                response = await client.post(
                    f"{self.executor_url}/execute",
                    json={
                        "code": chart.python_code,
                        "timeout": self.executor_timeout
                    }
                )
                
                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Executor service error: {response.text}"
                    }
                
                result = response.json()
                return result
                
        except httpx.TimeoutException:
            logger.error(f"Timeout executing chart {chart_id}")
            return {
                "success": False,
                "error": f"Execution timeout (>{self.executor_timeout}s)"
            }
        except Exception as e:
            logger.error(f"Error executing chart {chart_id}: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Execution failed: {str(e)}"
            }


# Глобальный экземпляр сервиса
dashboard_service = DashboardService()

