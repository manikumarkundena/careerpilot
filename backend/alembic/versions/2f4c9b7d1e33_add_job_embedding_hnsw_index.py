"""add pgvector HNSW index for job retrieval

Revision ID: 2f4c9b7d1e33
Revises: 8c1d6a7e9b20
Create Date: 2026-10-07 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op


revision: str = "2f4c9b7d1e33"
down_revision: Union[str, Sequence[str], None] = "8c1d6a7e9b20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_semantic_embeddings_job_hnsw
        ON semantic_embeddings
        USING hnsw (embedding vector_cosine_ops)
        WHERE entity_type = 'job'
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP INDEX IF EXISTS ix_semantic_embeddings_job_hnsw"
    )
