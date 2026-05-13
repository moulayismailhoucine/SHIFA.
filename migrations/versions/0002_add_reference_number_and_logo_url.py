"""Add reference_number to ordonnances and logo_url to doctors.

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add logo_url to doctors table
    op.add_column('doctors', sa.Column('logo_url', sa.String(length=500), nullable=True))
    
    # Add reference_number to ordonnances table
    op.add_column('ordonnances', sa.Column('reference_number', sa.String(length=50), nullable=True))
    op.create_index(op.f('ix_ordonnances_reference_number'), 'ordonnances', ['reference_number'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_ordonnances_reference_number'), table_name='ordonnances')
    op.drop_column('ordonnances', 'reference_number')
    op.drop_column('doctors', 'logo_url')
