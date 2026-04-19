"""semantic cache pgvector embeddings

Revision ID: 0004_semantic_cache_pgvector
Revises: 0003_api_keys
Create Date: 2026-04-19 05:40:00.000000
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = "0004_semantic_cache_pgvector"
down_revision = "0003_api_keys"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column(
        "semantic_cache_entries",
        sa.Column("embedding_vector", Vector(768), nullable=True),
    )
    op.execute(
        "UPDATE semantic_cache_entries SET embedding_vector = NULL"
    )
    op.drop_column("semantic_cache_entries", "embedding")
    op.alter_column(
        "semantic_cache_entries",
        "embedding_vector",
        new_column_name="embedding",
        existing_type=Vector(768),
        nullable=True,
    )


def downgrade() -> None:
    op.add_column(
        "semantic_cache_entries",
        sa.Column("embedding_text", sa.Text(), nullable=True),
    )
    op.drop_column("semantic_cache_entries", "embedding")
    op.alter_column(
        "semantic_cache_entries",
        "embedding_text",
        new_column_name="embedding",
        existing_type=sa.Text(),
        nullable=False,
    )
