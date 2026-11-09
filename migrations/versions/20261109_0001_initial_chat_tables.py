"""initial_chat_tables

Revision ID: 20261109_0001
Revises: 
Create Date: 2026-11-09 18:45:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20261109_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure pgcrypto extension is available for gen_random_uuid()
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    # =========================================================================
    # 1. Table: conversations (Created first without circular FK)
    # =========================================================================
    op.create_table(
        "conversations",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "title",
            sa.String(length=255),
            server_default="New Conversation",
            nullable=False,
        ),
        sa.Column(
            "title_source",
            sa.String(length=20),
            server_default="default",
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="active",
            nullable=False,
        ),
        sa.Column(
            "is_pinned",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "last_message_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "next_sequence_number",
            sa.BigInteger(),
            server_default="1",
            nullable=False,
        ),
        sa.Column(
            "generation_status",
            sa.String(length=20),
            server_default="idle",
            nullable=False,
        ),
        sa.Column(
            "active_generation_message_id",
            sa.Uuid(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CLOCK_TIMESTAMP()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CLOCK_TIMESTAMP()"),
            nullable=False,
        ),
        sa.Column(
            "deleted_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        sa.CheckConstraint(
            "status IN ('active', 'archived')",
            name=op.f("chk_conversations_status"),
        ),
        sa.CheckConstraint(
            "generation_status IN ('idle', 'generating')",
            name=op.f("chk_conversations_generation_status"),
        ),
        sa.CheckConstraint(
            "title_source IN ('default', 'generated', 'user')",
            name=op.f("chk_conversations_title_source"),
        ),
        sa.CheckConstraint(
            "next_sequence_number >= 1",
            name=op.f("chk_conversations_next_seq"),
        ),
        sa.CheckConstraint(
            "(generation_status = 'idle' AND active_generation_message_id IS NULL) OR "
            "(generation_status = 'generating' AND active_generation_message_id IS NOT NULL)",
            name=op.f("chk_conversations_generation_ownership"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_conversations_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversations")),
        sa.UniqueConstraint("id", "user_id", name="uq_conversations_id_user"),
    )

    # Indexes on conversations
    op.create_index(
        "idx_conversations_user_active",
        "conversations",
        ["user_id", sa.text("is_pinned DESC"), sa.text("last_message_at DESC NULLS LAST")],
        unique=False,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "idx_conversations_user_id",
        "conversations",
        ["user_id"],
        unique=False,
    )

    # =========================================================================
    # 2. Table: messages (Created second)
    # =========================================================================
    op.create_table(
        "messages",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("sequence_number", sa.BigInteger(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), server_default="", nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("client_message_id", sa.Uuid(), nullable=True),
        sa.Column("parent_message_id", sa.Uuid(), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CLOCK_TIMESTAMP()"),
            nullable=False,
        ),
        sa.Column(
            "completed_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        sa.CheckConstraint(
            "role IN ('user', 'assistant', 'system')",
            name=op.f("chk_messages_role"),
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'streaming', 'completed', 'failed', 'interrupted')",
            name=op.f("chk_messages_status"),
        ),
        sa.CheckConstraint(
            "sequence_number >= 1",
            name=op.f("chk_messages_sequence"),
        ),
        sa.CheckConstraint(
            "client_message_id IS NULL OR role = 'user'",
            name=op.f("chk_messages_client_id_role"),
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            name=op.f("fk_messages_conversation_id_conversations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["parent_message_id"],
            ["messages.id"],
            name=op.f("fk_messages_parent_message_id_messages"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_messages")),
        sa.UniqueConstraint(
            "conversation_id",
            "sequence_number",
            name="uq_messages_conversation_sequence",
        ),
        sa.UniqueConstraint(
            "id",
            "conversation_id",
            name="uq_messages_id_conversation",
        ),
    )

    # Indexes on messages
    op.create_index(
        "uq_messages_conversation_client_msg_id",
        "messages",
        ["conversation_id", "client_message_id"],
        unique=True,
        postgresql_where=sa.text("client_message_id IS NOT NULL AND role = 'user'"),
    )
    op.create_index(
        "idx_messages_conv_status_created",
        "messages",
        ["conversation_id", "status", "created_at"],
        unique=False,
    )
    op.create_index(
        "idx_messages_parent_id",
        "messages",
        ["parent_message_id"],
        unique=False,
        postgresql_where=sa.text("parent_message_id IS NOT NULL"),
    )

    # =========================================================================
    # 3. Circular FK: Link conversations.active_generation_message_id to messages
    # =========================================================================
    op.create_foreign_key(
        "fk_conversations_active_generation_msg",
        "conversations",
        "messages",
        ["active_generation_message_id", "id"],
        ["id", "conversation_id"],
        ondelete="SET NULL",
        deferrable=True,
        initially="DEFERRED",
    )

    # =========================================================================
    # 4. Table: message_feedback
    # =========================================================================
    op.create_table(
        "message_feedback",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("message_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("rating", sa.SmallInteger(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CLOCK_TIMESTAMP()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "rating >= 1 AND rating <= 5",
            name=op.f("chk_feedback_rating"),
        ),
        sa.ForeignKeyConstraint(
            ["message_id", "conversation_id"],
            ["messages.id", "messages.conversation_id"],
            name="fk_feedback_message_owner",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id", "user_id"],
            ["conversations.id", "conversations.user_id"],
            name="fk_feedback_user_owner",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_message_feedback")),
        sa.UniqueConstraint(
            "message_id",
            "user_id",
            name="uq_feedback_message_user",
        ),
    )

    op.create_index(
        "idx_feedback_conversation_id",
        "message_feedback",
        ["conversation_id"],
        unique=False,
    )
    op.create_index(
        "idx_feedback_user_id",
        "message_feedback",
        ["user_id"],
        unique=False,
    )

    # =========================================================================
    # 5. Table: conversation_summaries
    # =========================================================================
    op.create_table(
        "conversation_summaries",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column(
            "version",
            sa.Integer(),
            server_default="1",
            nullable=False,
        ),
        sa.Column("summarized_through_sequence", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CLOCK_TIMESTAMP()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CLOCK_TIMESTAMP()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "version >= 1",
            name=op.f("chk_summaries_version"),
        ),
        sa.CheckConstraint(
            "summarized_through_sequence >= 1",
            name=op.f("chk_summaries_through_seq"),
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            name=op.f("fk_conversation_summaries_conversation_id_conversations"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversation_summaries")),
        sa.UniqueConstraint(
            "conversation_id",
            "version",
            name="uq_summaries_conversation_version",
        ),
    )


def downgrade() -> None:
    # 1. Drop conversation_summaries
    op.drop_table("conversation_summaries")

    # 2. Drop message_feedback
    op.drop_index("idx_feedback_user_id", table_name="message_feedback")
    op.drop_index("idx_feedback_conversation_id", table_name="message_feedback")
    op.drop_table("message_feedback")

    # 3. Drop circular foreign key constraint before dropping messages
    op.drop_constraint(
        "fk_conversations_active_generation_msg",
        "conversations",
        type_="foreignkey",
    )

    # 4. Drop messages
    op.drop_index(
        "idx_messages_parent_id",
        table_name="messages",
        postgresql_where=sa.text("parent_message_id IS NOT NULL"),
    )
    op.drop_index("idx_messages_conv_status_created", table_name="messages")
    op.drop_index(
        "uq_messages_conversation_client_msg_id",
        table_name="messages",
        postgresql_where=sa.text("client_message_id IS NOT NULL AND role = 'user'"),
    )
    op.drop_table("messages")

    # 5. Drop conversations
    op.drop_index("idx_conversations_user_id", table_name="conversations")
    op.drop_index(
        "idx_conversations_user_active",
        table_name="conversations",
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.drop_table("conversations")
