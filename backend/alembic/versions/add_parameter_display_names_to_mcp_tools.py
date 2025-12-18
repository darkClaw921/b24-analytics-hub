"""Add parameter_display_names to mcp_tools

Revision ID: add_parameter_display_names
Revises: add_custom_fields
Create Date: 2025-12-14 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_parameter_display_names'
down_revision: Union[str, None] = 'add_custom_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add parameter_display_names column to mcp_tools table (JSON field)
    # Check if column already exists (in case it was created manually)
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('mcp_tools')]
    
    if 'parameter_display_names' not in columns:
        op.add_column('mcp_tools', sa.Column('parameter_display_names', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove parameter_display_names column from mcp_tools table
    op.drop_column('mcp_tools', 'parameter_display_names')
