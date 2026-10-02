"""add semantic embeddings

Revision ID: 8c1d6a7e9b20
Revises: 5bce4f759782
Create Date: 2026-10-02 18:15:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8c1d6a7e9b20"
down_revision: Union[str, Sequence[str], None] = "5bce4f759782"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "semantic_embeddings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.UUID(), nullable=False),
        sa.Column("model", sa.String(length=150), nullable=False),
        sa.Column("dimension", sa.Integer(), nullable=False),
        sa.Column("source_hash", sa.String(length=64), nullable=False),
        sa.Column("embedding", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "entity_type",
            "entity_id",
            "model",
            name="uq_semantic_embeddings_entity_model",
        ),
    )
    op.create_index(
        "ix_semantic_embeddings_entity",
        "semantic_embeddings",
        ["entity_type", "entity_id"],
    )
    op.create_index(
        "ix_semantic_embeddings_source_hash",
        "semantic_embeddings",
        ["source_hash"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_semantic_embeddings_source_hash",
        table_name="semantic_embeddings",
    )
    op.drop_index(
        "ix_semantic_embeddings_entity",
        table_name="semantic_embeddings",
    )
    op.drop_table("semantic_embeddings")
    op.execute("DROP EXTENSION IF EXISTS vector")
