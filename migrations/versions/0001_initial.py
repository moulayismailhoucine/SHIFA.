"""Initial schema — all tables.

Revision ID: 0001
Revises:
Create Date: 2026-05-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use SQLAlchemy metadata from models to auto-generate DDL
    # This is a no-op migration — tables are created by Base.metadata.create_all
    # in development. For production, generate with:
    #   alembic revision --autogenerate -m "your message"
    pass


def downgrade() -> None:
    pass
