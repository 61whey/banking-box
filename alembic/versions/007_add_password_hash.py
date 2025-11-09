"""add password_hash to clients and teams

Revision ID: 007
Revises: 006
Create Date: 2025-01-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from passlib.context import CryptContext


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None

# Initialize password context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def upgrade():
    """
    Добавляет password_hash в таблицы clients и teams для безопасного хранения паролей
    """
    # 1. Добавить столбец password_hash в clients (nullable=True временно)
    op.add_column('clients', 
        sa.Column('password_hash', sa.String(255), nullable=True)
    )
    
    # 2. Захешировать пароль "password" для всех demo-client-*
    conn = op.get_bind()
    demo_hash = pwd_context.hash("password")
    
    # Обновить всех клиентов с person_id начинающихся на 'demo-'
    conn.execute(
        text("UPDATE clients SET password_hash = :hash WHERE person_id LIKE 'demo-%'"),
        {"hash": demo_hash}
    )
    
    # Обновить всех клиентов с person_id начинающихся на 'cli-'
    # (реальные клиенты банка - тоже используют пароль "password" для demo)
    conn.execute(
        text("UPDATE clients SET password_hash = :hash WHERE person_id LIKE 'cli-%'"),
        {"hash": demo_hash}
    )
    
    # Обновить клиентов команд (team###-#)
    # Для них тоже используем стандартный пароль "password"
    conn.execute(
        text("UPDATE clients SET password_hash = :hash WHERE person_id LIKE 'team%'"),
        {"hash": demo_hash}
    )
    
    # 3. Сделать поле NOT NULL после заполнения
    op.alter_column('clients', 'password_hash', nullable=False)
    
    # 4. Добавить столбец password_hash в teams (nullable=True временно)
    op.add_column('teams',
        sa.Column('password_hash', sa.String(255), nullable=True)
    )
    
    # 5. Захешировать существующий client_secret как password_hash для команд
    # Получить все команды и захешировать их client_secret
    teams = conn.execute(text("SELECT id, client_secret FROM teams"))
    for team in teams:
        team_hash = pwd_context.hash(team.client_secret)
        conn.execute(
            text("UPDATE teams SET password_hash = :hash WHERE id = :id"),
            {"hash": team_hash, "id": team.id}
        )
    
    # 6. Сделать поле NOT NULL после заполнения
    op.alter_column('teams', 'password_hash', nullable=False)


def downgrade():
    """
    Откат изменений - удаление password_hash из clients и teams
    """
    op.drop_column('clients', 'password_hash')
    op.drop_column('teams', 'password_hash')

