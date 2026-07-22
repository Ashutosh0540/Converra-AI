"""ai orchestration

Revision ID: 20260716_0003
Revises: 20260716_0002
Create Date: 2026-07-16 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260716_0003"
down_revision: str | None = "20260716_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    agent_type = postgresql.ENUM(
        "FAQ",
        "LEAD",
        "SCHEDULING",
        "SUMMARY",
        "ESCALATION",
        name="agent_type",
        create_type=False,
    )
    conversation_status = postgresql.ENUM(
        "ACTIVE",
        "ESCALATED",
        "CLOSED",
        name="conversation_status",
        create_type=False,
    )
    workflow_stage = postgresql.ENUM(
        "ROUTING",
        "RETRIEVAL",
        "EXECUTION",
        "VALIDATION",
        "MEMORY_UPDATE",
        "ESCALATED",
        "CLOSED",
        name="workflow_stage",
        create_type=False,
    )

    agent_type.create(op.get_bind(), checkfirst=True)
    conversation_status.create(op.get_bind(), checkfirst=True)
    workflow_stage.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "conversations",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("workflow_stage", workflow_stage, nullable=False),
        sa.Column("status", conversation_status, nullable=False),
        sa.Column("active_agent", agent_type, nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("memory", sa.JSON(), nullable=False),
        sa.Column("retrieved_documents", sa.JSON(), nullable=False),
        sa.Column("lead_information", sa.JSON(), nullable=False),
        sa.Column("booking_request", sa.JSON(), nullable=False),
        sa.Column("escalation_state", sa.JSON(), nullable=False),
        sa.Column("failure_count", sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_conversations_organization_id"),
        "conversations",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_conversations_user_id"),
        "conversations",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "conversation_summaries",
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("source_agent", sa.String(length=50), nullable=False),
        sa.Column("is_final", sa.Boolean(), nullable=False),
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
            ["conversation_id"],
            ["conversations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_conversation_summaries_conversation_id"),
        "conversation_summaries",
        ["conversation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_conversation_summaries_organization_id"),
        "conversation_summaries",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_conversation_summaries_user_id"),
        "conversation_summaries",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_conversation_summaries_user_id"),
        table_name="conversation_summaries",
    )
    op.drop_index(
        op.f("ix_conversation_summaries_organization_id"),
        table_name="conversation_summaries",
    )
    op.drop_index(
        op.f("ix_conversation_summaries_conversation_id"),
        table_name="conversation_summaries",
    )
    op.drop_table("conversation_summaries")
    op.drop_index(op.f("ix_conversations_user_id"), table_name="conversations")
    op.drop_index(
        op.f("ix_conversations_organization_id"),
        table_name="conversations",
    )
    op.drop_table("conversations")
    postgresql.ENUM(name="workflow_stage").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="conversation_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="agent_type").drop(op.get_bind(), checkfirst=True)
