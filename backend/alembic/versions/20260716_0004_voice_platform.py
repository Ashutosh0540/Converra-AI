"""voice platform

Revision ID: 20260716_0004
Revises: 20260716_0003
Create Date: 2026-07-16 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260716_0004"
down_revision: str | None = "20260716_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    voice_agent_type = postgresql.ENUM(
        "FAQ",
        "LEAD",
        "SCHEDULING",
        "SUMMARY",
        "ESCALATION",
        name="voice_agent_type",
        create_type=False,
    )
    voice_workflow_stage = postgresql.ENUM(
        "ROUTING",
        "RETRIEVAL",
        "EXECUTION",
        "VALIDATION",
        "MEMORY_UPDATE",
        "ESCALATED",
        "CLOSED",
        name="voice_workflow_stage",
        create_type=False,
    )
    voice_session_status = postgresql.ENUM(
        "ACTIVE",
        "ESCALATED",
        "CLOSED",
        name="voice_session_status",
        create_type=False,
    )

    voice_agent_type.create(op.get_bind(), checkfirst=True)
    voice_workflow_stage.create(op.get_bind(), checkfirst=True)
    voice_session_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "voice_sessions",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("active_agent", voice_agent_type, nullable=True),
        sa.Column("workflow_stage", voice_workflow_stage, nullable=False),
        sa.Column("status", voice_session_status, nullable=False),
        sa.Column("transcript", sa.JSON(), nullable=False),
        sa.Column("memory_snapshot", sa.JSON(), nullable=False),
        sa.Column("current_transcript", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("active_user_id", sa.Uuid(), nullable=False),
        sa.Column("connection_count", sa.Integer(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["active_user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_voice_sessions_conversation_id"),
        "voice_sessions",
        ["conversation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_voice_sessions_organization_id"),
        "voice_sessions",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_voice_sessions_user_id"),
        "voice_sessions",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_voice_sessions_active_user_id"),
        "voice_sessions",
        ["active_user_id"],
        unique=False,
    )

    op.create_table(
        "voice_transcripts",
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("partial", sa.Boolean(), nullable=False),
        sa.Column("agent", sa.String(length=50), nullable=True),
        sa.Column("extra_metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["voice_sessions.id"],
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
        op.f("ix_voice_transcripts_session_id"),
        "voice_transcripts",
        ["session_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_voice_transcripts_organization_id"),
        "voice_transcripts",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_voice_transcripts_user_id"),
        "voice_transcripts",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_voice_transcripts_user_id"),
        table_name="voice_transcripts",
    )
    op.drop_index(
        op.f("ix_voice_transcripts_organization_id"),
        table_name="voice_transcripts",
    )
    op.drop_index(
        op.f("ix_voice_transcripts_session_id"),
        table_name="voice_transcripts",
    )
    op.drop_table("voice_transcripts")

    op.drop_index(
        op.f("ix_voice_sessions_active_user_id"),
        table_name="voice_sessions",
    )
    op.drop_index(
        op.f("ix_voice_sessions_user_id"),
        table_name="voice_sessions",
    )
    op.drop_index(
        op.f("ix_voice_sessions_organization_id"),
        table_name="voice_sessions",
    )
    op.drop_index(
        op.f("ix_voice_sessions_conversation_id"),
        table_name="voice_sessions",
    )
    op.drop_table("voice_sessions")
    postgresql.ENUM(name="voice_session_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="voice_workflow_stage").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="voice_agent_type").drop(op.get_bind(), checkfirst=True)
