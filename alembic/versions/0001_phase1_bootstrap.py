"""phase1 bootstrap

Revision ID: 0001_phase1_bootstrap
Revises:
Create Date: 2026-04-17 00:00:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_phase1_bootstrap"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS vector;")
