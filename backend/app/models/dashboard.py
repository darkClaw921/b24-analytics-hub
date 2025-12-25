"""
Dashboard and Chart models
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class ChartType(str, enum.Enum):
    """Chart type enum"""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"


class Dashboard(Base):
    """Dashboard model for storing user dashboards"""
    __tablename__ = "dashboards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="dashboards")
    charts = relationship("Chart", back_populates="dashboard", cascade="all, delete-orphan", order_by="Chart.created_at")

    def __repr__(self):
        return f"<Dashboard(id={self.id}, title='{self.title}', user_id={self.user_id})>"


class Chart(Base):
    """Chart model for storing charts in dashboards"""
    __tablename__ = "charts"

    id = Column(Integer, primary_key=True, index=True)
    dashboard_id = Column(Integer, ForeignKey("dashboards.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    chart_type = Column(Enum(ChartType), nullable=False)
    position_x = Column(Integer, default=0, nullable=False)
    position_y = Column(Integer, default=0, nullable=False)
    width = Column(Integer, default=400, nullable=False)
    height = Column(Integer, default=300, nullable=False)
    python_code = Column(Text, nullable=False)
    config = Column(JSON, nullable=True)  # Конфигурация чарта (цвета, настройки отображения)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    dashboard = relationship("Dashboard", back_populates="charts")

    def __repr__(self):
        return f"<Chart(id={self.id}, title='{self.title}', chart_type='{self.chart_type}', dashboard_id={self.dashboard_id})>"

