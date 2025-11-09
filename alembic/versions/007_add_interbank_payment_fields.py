"""add interbank payment fields to payments table

Revision ID: 007
Revises: 006
Create Date: 2025-01-29 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add interbank payment fields to payments table
    op.add_column('payments', sa.Column('payment_direction', sa.Text(), nullable=True))
    op.add_column('payments', sa.Column('source_bank_id', sa.Integer(), nullable=True))
    op.add_column('payments', sa.Column('source_bank', sa.Text(), nullable=True))
    op.add_column('payments', sa.Column('source_account', sa.Text(), nullable=True))
    op.add_column('payments', sa.Column('destination_bank_id', sa.Integer(), nullable=True))
    op.add_column('payments', sa.Column('external_payment_id', sa.Text(), nullable=True))
    op.add_column('payments', sa.Column('interbank_transfer_id', sa.Text(), nullable=True))
    op.add_column('payments', sa.Column('instruction_identification', sa.Text(), nullable=True))
    op.add_column('payments', sa.Column('end_to_end_identification', sa.Text(), nullable=True))
    op.add_column('payments', sa.Column('debtor_name', sa.Text(), nullable=True))
    op.add_column('payments', sa.Column('creditor_name', sa.Text(), nullable=True))
    op.add_column('payments', sa.Column('remittance_information', sa.Text(), nullable=True))
    
    # Alter account_id column to be nullable
    op.alter_column('payments', 'account_id',
                    existing_type=sa.Integer(),
                    nullable=True,
                    existing_nullable=False)


def downgrade() -> None:
    # Alter account_id column back to not nullable
    op.alter_column('payments', 'account_id',
                    existing_type=sa.Integer(),
                    nullable=False,
                    existing_nullable=True)
    
    # Drop interbank payment fields
    op.drop_column('payments', 'remittance_information')
    op.drop_column('payments', 'creditor_name')
    op.drop_column('payments', 'debtor_name')
    op.drop_column('payments', 'end_to_end_identification')
    op.drop_column('payments', 'instruction_identification')
    op.drop_column('payments', 'interbank_transfer_id')
    op.drop_column('payments', 'external_payment_id')
    op.drop_column('payments', 'destination_bank_id')
    op.drop_column('payments', 'source_account')
    op.drop_column('payments', 'source_bank')
    op.drop_column('payments', 'source_bank_id')
    op.drop_column('payments', 'payment_direction')

