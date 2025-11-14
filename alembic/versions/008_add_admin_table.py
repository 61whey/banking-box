"""add admin table

Revision ID: 008
Revises: 007
Create Date: 2025-01-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None

# Фиксированный bcrypt хеш для пароля админа "74m2C_X_cJa"
ADMIN_PASSWORD_HASH = '$2b$12$mTFsKxvml1fmoxhz/Sdzr.AA5iI6Nyy7m1HiBuO8mc47VXZdUEbbK'


def upgrade():
    """
    Создает таблицу admins и добавляет одного администратора по умолчанию
    """
    conn = op.get_bind()
    
    # 1. Проверяем, существует ли таблица
    result = conn.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_name='admins'
    """))
    
    if not result.fetchone():
        # Создаем таблицу admins
        op.create_table(
            'admins',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('username', sa.String(100), nullable=False),
            sa.Column('password_hash', sa.String(255), nullable=False),
            sa.Column('full_name', sa.String(255), nullable=True),
            sa.Column('email', sa.String(255), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
            sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('NOW()')),
            sa.Column('last_login', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('username')
        )
    
    # 2. Добавляем администратора по умолчанию (если его еще нет)
    result = conn.execute(text("SELECT username FROM admins WHERE username = 'admin'"))
    if not result.fetchone():
        conn.execute(
            text("""
                INSERT INTO admins (username, password_hash, full_name, is_active, created_at) 
                VALUES (:username, :password_hash, :full_name, :is_active, :created_at)
            """),
            {
                "username": "admin",
                "password_hash": ADMIN_PASSWORD_HASH,
                "full_name": "System Administrator",
                "is_active": True,
                "created_at": datetime.utcnow()
            }
        )


def downgrade():
    """
    Откат изменений - удаление таблицы admins
    """
    op.drop_table('admins')

