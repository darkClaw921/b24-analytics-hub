"""Add custom_name and custom_description to mcp_tools

Revision ID: add_custom_fields
Revises: f3382ab8d966
Create Date: 2025-12-12 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_custom_fields'
down_revision: Union[str, None] = 'f3382ab8d966'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add custom_name and custom_description columns to mcp_tools table
    op.add_column('mcp_tools', sa.Column('custom_name', sa.String(length=255), nullable=True))
    op.add_column('mcp_tools', sa.Column('custom_description', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove custom_name and custom_description columns from mcp_tools table
    op.drop_column('mcp_tools', 'custom_description')
    op.drop_column('mcp_tools', 'custom_name')

