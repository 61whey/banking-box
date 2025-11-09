"""seed banks

Revision ID: 004
Revises: 003
Create Date: 2025-11-08 22:10:00.000000

"""
from alembic import op
import csv
import os


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Get the path to the CSV file
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'banks.csv')

    # Read CSV and prepare data
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        banks_data = []
        for row in reader:
            # Convert string 'True'/'False' to boolean
            external = row['external'] == 'True'
            # Handle empty description
            description = row['description'] if row['description'] else None

            banks_data.append({
                'id': int(row['id']),
                'external': external,
                'code': row['code'],
                'name': row['name'],
                'description': description,
                'api_url': row['api_url'],
                'api_user': row['api_user'],
                'api_secret': row['api_secret']
            })

    # Insert data using bulk insert with WHERE NOT EXISTS pattern
    if banks_data:
        # Build VALUES clause
        values_list = []
        for bank in banks_data:
            description = f"'{bank['description']}'" if bank['description'] else "NULL"
            values_list.append(
                f"({bank['id']}, {bank['external']}, '{bank['code']}', '{bank['name']}', "
                f"{description}, '{bank['api_url']}', '{bank['api_user']}', '{bank['api_secret']}')"
            )

        values_clause = ',\n            '.join(values_list)

        op.execute(f"""
            INSERT INTO banks (id, external, code, name, description, api_url, api_user, api_secret)
            SELECT * FROM (VALUES
                {values_clause}
            ) AS v(id, external, code, name, description, api_url, api_user, api_secret)
            WHERE NOT EXISTS (SELECT 1 FROM banks WHERE banks.id = v.id)
        """)


def downgrade() -> None:
    # Delete only the banks that were inserted by this migration
    op.execute("""
        DELETE FROM banks WHERE id IN (1, 2, 3)
    """)
