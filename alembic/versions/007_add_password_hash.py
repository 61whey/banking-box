"""add password_hash to clients and teams

Revision ID: 007
Revises: 006
Create Date: 2025-01-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None

# Фиксированный bcrypt хеш для пароля "password"
# Используем один и тот же хеш для идемпотентности миграции
PASSWORD_HASH = '$2b$12$dWnVVAjnwluYi97NaclEbO/ZfVG6QYLIzqwr.OUDFtZU8MuLH40oq'


def upgrade():
    """
    Добавляет password_hash в таблицы clients и teams для безопасного хранения паролей
    """
    conn = op.get_bind()
    
    # 1. Добавить столбец password_hash в clients (nullable=True временно)
    # Проверяем, существует ли столбец
    result = conn.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='clients' AND column_name='password_hash'
    """))
    if not result.fetchone():
        op.add_column('clients', 
            sa.Column('password_hash', sa.String(255), nullable=True)
        )
    
    # 2. Обновить password_hash для всех клиентов с единым паролем "password"
    # Обновляем только те записи, где password_hash IS NULL
    
    # Обновить всех клиентов с person_id начинающихся на 'demo-'
    conn.execute(
        text("UPDATE clients SET password_hash = :hash WHERE person_id LIKE 'demo-%' AND password_hash IS NULL"),
        {"hash": PASSWORD_HASH}
    )
    
    # Обновить всех клиентов с person_id начинающихся на 'cli-'
    # (реальные клиенты банка - тоже используют пароль "password" для demo)
    conn.execute(
        text("UPDATE clients SET password_hash = :hash WHERE person_id LIKE 'cli-%' AND password_hash IS NULL"),
        {"hash": PASSWORD_HASH}
    )
    
    # Обновить клиентов команд (team###-#)
    # Для них тоже используем стандартный пароль "password"
    conn.execute(
        text("UPDATE clients SET password_hash = :hash WHERE person_id LIKE 'team%' AND password_hash IS NULL"),
        {"hash": PASSWORD_HASH}
    )
    
    # 3. Сделать поле NOT NULL после заполнения
    op.alter_column('clients', 'password_hash', nullable=False)
    
    # 4. Добавить столбец password_hash в teams (nullable=True временно)
    # Проверяем, существует ли столбец
    result = conn.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='teams' AND column_name='password_hash'
    """))
    if not result.fetchone():
        op.add_column('teams',
            sa.Column('password_hash', sa.String(255), nullable=True)
        )
    
    # 5. Для команд используем тот же пароль "password"
    # Обновляем только те записи, где password_hash IS NULL
    conn.execute(
        text("UPDATE teams SET password_hash = :hash WHERE password_hash IS NULL"),
        {"hash": PASSWORD_HASH}
    )
    
    # 6. Сделать поле NOT NULL после заполнения
    op.alter_column('teams', 'password_hash', nullable=False)


def downgrade():
    """
    Откат изменений - удаление password_hash из clients и teams
    """
    op.drop_column('clients', 'password_hash')
    op.drop_column('teams', 'password_hash')

