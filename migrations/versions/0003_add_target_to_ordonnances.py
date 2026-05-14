"""Add target field to ordonnances (pharmacy vs lab).

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add target column to ordonnances table
    op.add_column('ordonnances', sa.Column('target', sa.String(length=20), nullable=True, server_default='pharmacy'))


def downgrade() -> None:
    op.drop_column('ordonnances', 'target')
