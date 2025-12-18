"""Add hidden_parameters to mcp_tools

Revision ID: add_hidden_parameters
Revises: add_parameter_display_names
Create Date: 2025-12-14 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_hidden_parameters'
down_revision: Union[str, None] = 'add_parameter_display_names'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add hidden_parameters column to mcp_tools table (JSON field)
    # Check if column already exists (in case it was created manually)
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('mcp_tools')]
    
    if 'hidden_parameters' not in columns:
        op.add_column('mcp_tools', sa.Column('hidden_parameters', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove hidden_parameters column from mcp_tools table
    op.drop_column('mcp_tools', 'hidden_parameters')

