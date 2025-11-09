"""add client_id_external and make client_id nullable

Revision ID: 006
Revises: 005
Create Date: 2025-01-29 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add client_id_external column to consents table
    op.add_column('consents', sa.Column('client_id_external', sa.Text(), nullable=True))
    
    # Alter client_id column to be nullable
    op.alter_column('consents', 'client_id',
                    existing_type=sa.Integer(),
                    nullable=True,
                    existing_nullable=False)


def downgrade() -> None:
    # Alter client_id column back to not nullable
    op.alter_column('consents', 'client_id',
                    existing_type=sa.Integer(),
                    nullable=False,
                    existing_nullable=True)
    
    # Drop client_id_external column
    op.drop_column('consents', 'client_id_external')

