"""initial_schema

Revision ID: 001_initial
Revises: 
Create Date: 2025-01-29 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Teams
    op.create_table('teams',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('client_id', sa.String(length=100), nullable=False),
        sa.Column('client_secret', sa.String(length=255), nullable=False),
        sa.Column('team_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_id')
    )

    # Clients
    op.create_table('clients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('person_id', sa.String(length=100), nullable=True),
        sa.Column('client_type', sa.String(length=20), nullable=True),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('segment', sa.String(length=50), nullable=True),
        sa.Column('birth_year', sa.Integer(), nullable=True),
        sa.Column('monthly_income', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('person_id')
    )

    # Accounts
    op.create_table('accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('account_number', sa.String(length=20), nullable=False),
        sa.Column('account_type', sa.String(length=50), nullable=True),
        sa.Column('balance', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('opened_at', sa.DateTime(), nullable=True, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('account_number')
    )

    # Transactions
    op.create_table('transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('transaction_id', sa.String(length=100), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('direction', sa.String(length=10), nullable=True),
        sa.Column('counterparty', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('transaction_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('transaction_id')
    )

    # Bank Settings
    op.create_table('bank_settings',
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('key')
    )

    # Auth Tokens
    op.create_table('auth_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('token_type', sa.String(length=20), nullable=True),
        sa.Column('subject_id', sa.String(length=100), nullable=True),
        sa.Column('token_hash', sa.String(length=255), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Consent Requests
    op.create_table('consent_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('request_id', sa.String(length=100), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('requesting_bank', sa.String(length=100), nullable=True),
        sa.Column('requesting_bank_name', sa.String(length=255), nullable=True),
        sa.Column('permissions', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('responded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('request_id')
    )

    # Consents
    op.create_table('consents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('consent_id', sa.String(length=100), nullable=False),
        sa.Column('request_id', sa.Integer(), nullable=True),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('granted_to', sa.String(length=100), nullable=False),
        sa.Column('permissions', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('expiration_date_time', sa.DateTime(), nullable=True),
        sa.Column('creation_date_time', sa.DateTime(), nullable=True),
        sa.Column('status_update_date_time', sa.DateTime(), nullable=True),
        sa.Column('signed_at', sa.DateTime(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('last_accessed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['request_id'], ['consent_requests.id'], ),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('consent_id')
    )

    # Notifications
    op.create_table('notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.String(length=50), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('related_id', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Payment Consent Requests
    op.create_table('payment_consent_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('request_id', sa.String(length=100), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('requesting_bank', sa.String(length=100), nullable=True),
        sa.Column('requesting_bank_name', sa.String(length=255), nullable=True),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=True),
        sa.Column('debtor_account', sa.String(length=255), nullable=True),
        sa.Column('creditor_account', sa.String(length=255), nullable=True),
        sa.Column('creditor_name', sa.String(length=255), nullable=True),
        sa.Column('reference', sa.String(length=255), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('responded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('request_id')
    )

    # Payment Consents
    op.create_table('payment_consents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('consent_id', sa.String(length=100), nullable=False),
        sa.Column('request_id', sa.Integer(), nullable=True),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('granted_to', sa.String(length=100), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=True),
        sa.Column('debtor_account', sa.String(length=255), nullable=True),
        sa.Column('creditor_account', sa.String(length=255), nullable=True),
        sa.Column('creditor_name', sa.String(length=255), nullable=True),
        sa.Column('reference', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('expiration_date_time', sa.DateTime(), nullable=True),
        sa.Column('creation_date_time', sa.DateTime(), nullable=True),
        sa.Column('status_update_date_time', sa.DateTime(), nullable=True),
        sa.Column('signed_at', sa.DateTime(), nullable=True),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['request_id'], ['payment_consent_requests.id'], ),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('consent_id')
    )

    # Product Agreement Consent Requests
    op.create_table('product_agreement_consent_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('request_id', sa.String(length=100), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('requesting_bank', sa.String(length=100), nullable=True),
        sa.Column('requesting_bank_name', sa.String(length=255), nullable=True),
        sa.Column('read_product_agreements', sa.Boolean(), nullable=True),
        sa.Column('open_product_agreements', sa.Boolean(), nullable=True),
        sa.Column('close_product_agreements', sa.Boolean(), nullable=True),
        sa.Column('allowed_product_types', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('max_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('valid_until', sa.DateTime(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('responded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('request_id')
    )

    # Product Agreement Consents
    op.create_table('product_agreement_consents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('consent_id', sa.String(length=100), nullable=False),
        sa.Column('request_id', sa.Integer(), nullable=True),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('granted_to', sa.String(length=100), nullable=False),
        sa.Column('read_product_agreements', sa.Boolean(), nullable=True),
        sa.Column('open_product_agreements', sa.Boolean(), nullable=True),
        sa.Column('close_product_agreements', sa.Boolean(), nullable=True),
        sa.Column('allowed_product_types', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('max_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('current_total_opened', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('valid_until', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('creation_date_time', sa.DateTime(), nullable=True),
        sa.Column('status_update_date_time', sa.DateTime(), nullable=True),
        sa.Column('signed_at', sa.DateTime(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['request_id'], ['product_agreement_consent_requests.id'], ),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('consent_id')
    )

    # Payments
    op.create_table('payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('payment_id', sa.String(length=100), nullable=False),
        sa.Column('payment_consent_id', sa.String(length=100), nullable=True),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=True),
        sa.Column('destination_account', sa.String(length=255), nullable=True),
        sa.Column('destination_bank', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('creation_date_time', sa.DateTime(), nullable=True),
        sa.Column('status_update_date_time', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('payment_id')
    )

    # Interbank Transfers
    op.create_table('interbank_transfers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('transfer_id', sa.String(length=100), nullable=False),
        sa.Column('payment_id', sa.String(length=100), nullable=True),
        sa.Column('from_bank', sa.String(length=100), nullable=False),
        sa.Column('to_bank', sa.String(length=100), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.payment_id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('transfer_id')
    )

    # Bank Capital
    op.create_table('bank_capital',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bank_code', sa.String(length=100), nullable=False),
        sa.Column('capital', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('initial_capital', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('total_deposits', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('total_loans', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('bank_code')
    )

    # Products
    op.create_table('products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.String(length=100), nullable=False),
        sa.Column('product_type', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('interest_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('min_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('max_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('term_months', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_id')
    )

    # Product Agreements
    op.create_table('product_agreements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agreement_id', sa.String(length=100), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=True),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('agreement_id')
    )

    # Key Rate History
    op.create_table('key_rate_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rate', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('effective_from', sa.DateTime(), nullable=True),
        sa.Column('changed_by', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Customer Leads
    op.create_table('customer_leads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_lead_id', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('interested_products', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('estimated_income', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('contacted_at', sa.DateTime(), nullable=True),
        sa.Column('converted_to_client_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['converted_to_client_id'], ['clients.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('customer_lead_id')
    )

    # Product Offers
    op.create_table('product_offers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('offer_id', sa.String(length=100), nullable=False),
        sa.Column('customer_lead_id', sa.String(length=100), nullable=True),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('personalized_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('personalized_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('personalized_term_months', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('valid_until', sa.DateTime(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('viewed_at', sa.DateTime(), nullable=True),
        sa.Column('responded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['customer_lead_id'], ['customer_leads.customer_lead_id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('offer_id')
    )

    # Product Offer Consents
    op.create_table('product_offer_consents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('consent_id', sa.String(length=100), nullable=False),
        sa.Column('customer_lead_id', sa.String(length=100), nullable=True),
        sa.Column('client_id', sa.Integer(), nullable=True),
        sa.Column('permissions', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['customer_lead_id'], ['customer_leads.customer_lead_id'], ),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('consent_id')
    )

    # Product Applications
    op.create_table('product_applications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('application_id', sa.String(length=100), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('offer_id', sa.String(length=100), nullable=True),
        sa.Column('requested_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('requested_term_months', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('application_data', sa.Text(), nullable=True),
        sa.Column('decision', sa.String(length=50), nullable=True),
        sa.Column('decision_reason', sa.Text(), nullable=True),
        sa.Column('approved_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('approved_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('decision_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['offer_id'], ['product_offers.offer_id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('application_id')
    )

    # VRP Consents
    op.create_table('vrp_consents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('consent_id', sa.String(length=100), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('max_individual_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('max_amount_period', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('period_type', sa.String(length=20), nullable=True),
        sa.Column('max_payments_count', sa.Integer(), nullable=True),
        sa.Column('valid_from', sa.DateTime(), nullable=True),
        sa.Column('valid_to', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('authorised_at', sa.DateTime(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('consent_id')
    )

    # VRP Payments
    op.create_table('vrp_payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('payment_id', sa.String(length=100), nullable=False),
        sa.Column('vrp_consent_id', sa.String(length=100), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=True),
        sa.Column('destination_account', sa.String(length=255), nullable=False),
        sa.Column('destination_bank', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('is_recurring', sa.Boolean(), nullable=True),
        sa.Column('recurrence_frequency', sa.String(length=20), nullable=True),
        sa.Column('next_payment_date', sa.DateTime(), nullable=True),
        sa.Column('creation_date_time', sa.DateTime(), nullable=True),
        sa.Column('status_update_date_time', sa.DateTime(), nullable=True),
        sa.Column('executed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['vrp_consent_id'], ['vrp_consents.consent_id'], ),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('payment_id')
    )

    # API Call Log
    op.create_table('api_calls_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('caller_id', sa.String(length=100), nullable=True),
        sa.Column('caller_type', sa.String(length=50), nullable=True),
        sa.Column('person_id', sa.String(length=100), nullable=True),
        sa.Column('endpoint', sa.String(length=500), nullable=False),
        sa.Column('method', sa.String(length=10), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('synced_to_directory', sa.Boolean(), nullable=True),
        sa.Column('synced_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_api_calls_log_created_at'), 'api_calls_log', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_api_calls_log_created_at'), table_name='api_calls_log')
    op.drop_table('api_calls_log')
    op.drop_table('vrp_payments')
    op.drop_table('vrp_consents')
    op.drop_table('product_applications')
    op.drop_table('product_offer_consents')
    op.drop_table('product_offers')
    op.drop_table('customer_leads')
    op.drop_table('key_rate_history')
    op.drop_table('product_agreements')
    op.drop_table('products')
    op.drop_table('bank_capital')
    op.drop_table('interbank_transfers')
    op.drop_table('payments')
    op.drop_table('product_agreement_consents')
    op.drop_table('product_agreement_consent_requests')
    op.drop_table('payment_consents')
    op.drop_table('payment_consent_requests')
    op.drop_table('notifications')
    op.drop_table('consents')
    op.drop_table('consent_requests')
    op.drop_table('auth_tokens')
    op.drop_table('bank_settings')
    op.drop_table('transactions')
    op.drop_table('accounts')
    op.drop_table('clients')
    op.drop_table('teams')

