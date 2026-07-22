"""knowledge platform

Revision ID: 20260716_0002
Revises: 20260716_0001
Create Date: 2026-07-16 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260716_0002"
down_revision: str | None = "20260716_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    document_status = postgresql.ENUM(
        "PROCESSING",
        "READY",
        "FAILED",
        name="document_status",
        create_type=False,
    )
    document_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "knowledge_documents",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("uploader_id", sa.Uuid(), nullable=False),
        sa.Column("filename", sa.String(length=512), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("source", sa.String(length=512), nullable=False),
        sa.Column("status", document_status, nullable=False),
        sa.Column(
            "upload_time",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("chunk_count", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["uploader_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_knowledge_documents_organization_id"),
        "knowledge_documents",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_knowledge_documents_uploader_id"),
        "knowledge_documents",
        ["uploader_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_knowledge_documents_uploader_id"),
        table_name="knowledge_documents",
    )
    op.drop_index(
        op.f("ix_knowledge_documents_organization_id"),
        table_name="knowledge_documents",
    )
    op.drop_table("knowledge_documents")
    postgresql.ENUM(name="document_status").drop(op.get_bind(), checkfirst=True)
