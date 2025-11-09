"""add bank_id to consents

Revision ID: 005
Revises: 004
Create Date: 2025-01-29 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add bank_id column to consents table
    op.add_column('consents', sa.Column('bank_id', sa.Integer(), nullable=True))
    
    # Add foreign key constraint to banks.id
    op.create_foreign_key(
        'fk_consents_bank_id',
        'consents',
        'banks',
        ['bank_id'],
        ['id']
    )


def downgrade() -> None:
    # Drop foreign key constraint
    op.drop_constraint('fk_consents_bank_id', 'consents', type_='foreignkey')
    
    # Drop bank_id column
    op.drop_column('consents', 'bank_id')

