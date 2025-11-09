"""seed_data

Revision ID: 002_seed
Revises: 001_initial
Create Date: 2025-01-29 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_seed'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Клиенты команды team025 и demo клиенты
    op.execute("""
        INSERT INTO clients (person_id, client_type, full_name, segment, birth_year, monthly_income)
        SELECT * FROM (VALUES
            ('team025-1', 'individual', 'Участник команды №1', 'employee', 1995, 100000),
            ('team025-2', 'individual', 'Участник команды №2', 'employee', 1994, 110000),
            ('team025-3', 'individual', 'Участник команды №3', 'employee', 1993, 105000),
            ('team025-4', 'individual', 'Участник команды №4', 'entrepreneur', 1992, 150000),
            ('team025-5', 'individual', 'Участник команды №5', 'employee', 1996, 95000),
            ('team025-6', 'individual', 'Участник команды №6', 'employee', 1997, 90000),
            ('team025-7', 'individual', 'Участник команды №7', 'employee', 1991, 120000),
            ('team025-8', 'individual', 'Участник команды №8', 'employee', 1998, 85000),
            ('team025-9', 'individual', 'Участник команды №9', 'entrepreneur', 1990, 200000),
            ('team025-10', 'individual', 'Участник команды №10', 'employee', 1999, 80000),
            ('demo-client-001', 'individual', 'Демо клиент №1', 'employee', 1988, 120000),
            ('demo-client-002', 'individual', 'Демо клиент №2', 'employee', 1982, 150000),
            ('demo-client-003', 'individual', 'Демо клиент №3', 'entrepreneur', 1975, 200000)
        ) AS v(person_id, client_type, full_name, segment, birth_year, monthly_income)
        WHERE NOT EXISTS (SELECT 1 FROM clients WHERE clients.person_id = v.person_id)
    """)

    # Счета для команды team025 и demo клиентов
    op.execute("""
        INSERT INTO accounts (client_id, account_number, account_type, balance, currency, status)
        SELECT * FROM (VALUES
            (1, '40817810200000000001', 'checking', 500000.00, 'RUB', 'active'),
            (2, '40817810200000000002', 'checking', 450000.00, 'RUB', 'active'),
            (3, '40817810200000000003', 'checking', 480000.00, 'RUB', 'active'),
            (4, '40817810200000000004', 'checking', 600000.00, 'RUB', 'active'),
            (5, '40817810200000000005', 'checking', 350000.00, 'RUB', 'active'),
            (6, '40817810200000000006', 'checking', 320000.00, 'RUB', 'active'),
            (7, '40817810200000000007', 'checking', 550000.00, 'RUB', 'active'),
            (8, '40817810200000000008', 'checking', 280000.00, 'RUB', 'active'),
            (9, '40817810200000000009', 'checking', 750000.00, 'RUB', 'active'),
            (10, '40817810200000000010', 'checking', 420000.00, 'RUB', 'active'),
            (11, '40817810099920011001', 'checking', 320000.00, 'RUB', 'active'),
            (12, '40817810099920012001', 'checking', 450000.50, 'RUB', 'active'),
            (13, '40817810099920013001', 'checking', 550000.75, 'RUB', 'active')
        ) AS v(client_id, account_number, account_type, balance, currency, status)
        WHERE NOT EXISTS (SELECT 1 FROM accounts WHERE accounts.account_number = v.account_number)
    """)

    # Транзакции для team025 и demo клиентов
    op.execute("""
        INSERT INTO transactions (account_id, transaction_id, amount, direction, counterparty, description, transaction_date)
        SELECT * FROM (VALUES
            (1, 'tx-team025-001', 100000.00, 'credit', 'ООО Работодатель', 'Зарплата', '2025-10-01 10:00:00'::timestamp),
            (2, 'tx-team025-002', 110000.00, 'credit', 'ООО Компания', 'Зарплата', '2025-10-01 10:00:00'::timestamp),
            (3, 'tx-team025-003', 105000.00, 'credit', 'ООО Работодатель', 'Зарплата', '2025-10-01 10:00:00'::timestamp),
            (4, 'tx-team025-004', 150000.00, 'credit', 'Клиенты', 'Доход от бизнеса', '2025-09-30 18:00:00'::timestamp),
            (5, 'tx-team025-005', 95000.00, 'credit', 'ООО Работодатель', 'Зарплата', '2025-10-01 10:00:00'::timestamp),
            (6, 'tx-team025-006', 90000.00, 'credit', 'ООО Компания', 'Зарплата', '2025-10-01 10:00:00'::timestamp),
            (7, 'tx-team025-007', 120000.00, 'credit', 'ООО Работодатель', 'Зарплата', '2025-10-01 10:00:00'::timestamp),
            (8, 'tx-team025-008', 85000.00, 'credit', 'ООО Компания', 'Зарплата', '2025-10-01 10:00:00'::timestamp),
            (9, 'tx-team025-009', 200000.00, 'credit', 'Клиенты', 'Доход от бизнеса', '2025-09-30 18:00:00'::timestamp),
            (10, 'tx-team025-010', 80000.00, 'credit', 'ООО Работодатель', 'Зарплата', '2025-10-01 10:00:00'::timestamp),
            (11, 'tx-demo-001', 120000.00, 'credit', 'ООО Работодатель', 'Зарплата', '2025-10-01 10:00:00'::timestamp),
            (12, 'tx-demo-002', 150000.00, 'credit', 'ООО Компания', 'Зарплата', '2025-10-01 10:00:00'::timestamp),
            (13, 'tx-demo-003', 200000.00, 'credit', 'Клиенты', 'Доход от бизнеса', '2025-09-30 18:00:00'::timestamp)
        ) AS v(account_id, transaction_id, amount, direction, counterparty, description, transaction_date)
        WHERE NOT EXISTS (SELECT 1 FROM transactions WHERE transactions.transaction_id = v.transaction_id)
    """)

    # Настройки банка
    op.execute("""
        INSERT INTO bank_settings (key, value)
        VALUES
            ('bank_code', 'convolute'),
            ('bank_name', 'Convolute'),
            ('public_address', 'http://localhost:8000'),
            ('capital', '3500000.00'),
            ('key_rate', '7.50'),
            ('auto_approve_consents', 'true')
        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
    """)

    # Капитал банка
    op.execute("""
        INSERT INTO bank_capital (bank_code, capital, initial_capital, total_deposits, total_loans)
        VALUES ('convolute', 3500000.00, 3500000.00, 0, 0)
        ON CONFLICT (bank_code) DO NOTHING
    """)

    # Продукты банка
    op.execute("""
        INSERT INTO products (product_id, product_type, name, description, interest_rate, min_amount, term_months)
        SELECT * FROM (VALUES
            ('prod-ab-deposit-001', 'deposit', 'Выгодный депозит', 'Ставка 9.0% годовых', 9.0, 100000, 12),
            ('prod-ab-card-001', 'card', 'Кредитная карта Gold', 'Ставка 16.5%, кэшбэк 3%', 16.5, 0, NULL),
            ('prod-ab-loan-001', 'loan', 'Кредит наличными', 'Ставка 13.5% годовых', 13.5, 100000, 24)
        ) AS v(product_id, product_type, name, description, interest_rate, min_amount, term_months)
        WHERE NOT EXISTS (SELECT 1 FROM products WHERE products.product_id = v.product_id)
    """)

    # История ключевой ставки ЦБ
    op.execute("""
        INSERT INTO key_rate_history (rate, changed_by)
        SELECT 7.50, 'system'
        WHERE NOT EXISTS (SELECT 1 FROM key_rate_history WHERE rate = 7.50 AND changed_by = 'system')
    """)

    # Команда team025
    op.execute("""
        INSERT INTO teams (client_id, client_secret, team_name, is_active)
        VALUES ('team025', 'clear_text_pass_wJzc24f9u2', 'Команда 025', true)
        ON CONFLICT (client_id) DO NOTHING
    """)


def downgrade() -> None:
    # Удаляем seed данные в обратном порядке
    op.execute("DELETE FROM teams WHERE client_id = 'team025'")
    op.execute("DELETE FROM key_rate_history WHERE rate = 7.50 AND changed_by = 'system'")
    op.execute("DELETE FROM products WHERE product_id IN ('prod-ab-deposit-001', 'prod-ab-card-001', 'prod-ab-loan-001')")
    op.execute("DELETE FROM bank_capital WHERE bank_code = 'convolute'")
    op.execute("DELETE FROM bank_settings WHERE key IN ('bank_code', 'bank_name', 'public_address', 'capital', 'key_rate', 'auto_approve_consents')")
    op.execute("DELETE FROM transactions WHERE transaction_id LIKE 'tx-%'")
    # Delete accounts first, using client_id to ensure all accounts are deleted
    op.execute("""
        DELETE FROM accounts 
        WHERE client_id IN (
            SELECT id FROM clients 
            WHERE person_id LIKE 'team025-%' OR person_id LIKE 'demo-client-%'
        )
    """)
    op.execute("DELETE FROM clients WHERE person_id LIKE 'team025-%' OR person_id LIKE 'demo-client-%'")

