"""human in the loop platform

Revision ID: 20260719_0005
Revises: 20260716_0004
Create Date: 2026-07-19 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260719_0005"
down_revision: str | None = "20260716_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    escalation_priority = postgresql.ENUM(
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
        name="escalation_priority",
        create_type=False,
    )
    escalation_status = postgresql.ENUM(
        "PENDING",
        "ASSIGNED",
        "ACCEPTED",
        "IN_PROGRESS",
        "RESOLVED",
        "CLOSED",
        name="escalation_status",
        create_type=False,
    )
    escalation_action_type = postgresql.ENUM(
        "CREATED",
        "ASSIGNED",
        "REASSIGNED",
        "ACCEPTED",
        "RESOLVED",
        "CLOSED",
        "TRANSFERRED",
        "AI_RECOMMENDATION",
        "OVERRIDE",
        name="escalation_action_type",
        create_type=False,
    )
    escalation_priority.create(op.get_bind(), checkfirst=True)
    escalation_status.create(op.get_bind(), checkfirst=True)
    escalation_action_type.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "conversations",
        sa.Column("human_mode", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "conversations",
        sa.Column("human_assignee_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "conversations",
        sa.Column("human_mode_started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_conversations_human_assignee_id_users",
        "conversations",
        "users",
        ["human_assignee_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "escalation_cases",
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("customer_name", sa.String(length=255), nullable=False),
        sa.Column("customer_email", sa.String(length=255), nullable=False),
        sa.Column("assigned_agent_id", sa.Uuid(), nullable=True),
        sa.Column("escalation_reason", sa.Text(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("priority", escalation_priority, nullable=False),
        sa.Column("status", escalation_status, nullable=False),
        sa.Column("source_channel", sa.String(length=20), nullable=False),
        sa.Column("source_agent", sa.String(length=50), nullable=True),
        sa.Column("human_mode", sa.Boolean(), nullable=False),
        sa.Column("ai_confidence_snapshot", sa.JSON(), nullable=False),
        sa.Column("retrieved_sources", sa.JSON(), nullable=False),
        sa.Column("guardrail_result", sa.JSON(), nullable=False),
        sa.Column("escalation_decision", sa.JSON(), nullable=False),
        sa.Column("customer_context", sa.JSON(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.ForeignKeyConstraint(["customer_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["assigned_agent_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_escalation_cases_conversation_id"), "escalation_cases", ["conversation_id"], unique=False)
    op.create_index(op.f("ix_escalation_cases_organization_id"), "escalation_cases", ["organization_id"], unique=False)
    op.create_index(op.f("ix_escalation_cases_customer_id"), "escalation_cases", ["customer_id"], unique=False)
    op.create_index(op.f("ix_escalation_cases_assigned_agent_id"), "escalation_cases", ["assigned_agent_id"], unique=False)

    op.create_table(
        "escalation_audit_events",
        sa.Column("escalation_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("action", escalation_action_type, nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("before_state", sa.JSON(), nullable=False),
        sa.Column("after_state", sa.JSON(), nullable=False),
        sa.Column("extra_metadata", sa.JSON(), nullable=False),
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
            ["escalation_id"],
            ["escalation_cases.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_escalation_audit_events_escalation_id"), "escalation_audit_events", ["escalation_id"], unique=False)
    op.create_index(op.f("ix_escalation_audit_events_organization_id"), "escalation_audit_events", ["organization_id"], unique=False)
    op.create_index(op.f("ix_escalation_audit_events_actor_user_id"), "escalation_audit_events", ["actor_user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_escalation_audit_events_actor_user_id"), table_name="escalation_audit_events")
    op.drop_index(op.f("ix_escalation_audit_events_organization_id"), table_name="escalation_audit_events")
    op.drop_index(op.f("ix_escalation_audit_events_escalation_id"), table_name="escalation_audit_events")
    op.drop_table("escalation_audit_events")

    op.drop_index(op.f("ix_escalation_cases_assigned_agent_id"), table_name="escalation_cases")
    op.drop_index(op.f("ix_escalation_cases_customer_id"), table_name="escalation_cases")
    op.drop_index(op.f("ix_escalation_cases_organization_id"), table_name="escalation_cases")
    op.drop_index(op.f("ix_escalation_cases_conversation_id"), table_name="escalation_cases")
    op.drop_table("escalation_cases")

    op.drop_constraint(
        "fk_conversations_human_assignee_id_users",
        "conversations",
        type_="foreignkey",
    )
    op.drop_column("conversations", "human_mode_started_at")
    op.drop_column("conversations", "human_assignee_id")
    op.drop_column("conversations", "human_mode")

    postgresql.ENUM(name="escalation_action_type").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="escalation_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="escalation_priority").drop(op.get_bind(), checkfirst=True)
