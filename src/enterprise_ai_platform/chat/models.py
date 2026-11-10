"""
SQLAlchemy 2.x ORM models for the Chat / Conversation Management Module.

Defines the four module-owned tables:
1. conversations
2. messages
3. message_feedback
4. conversation_summaries
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    and_,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from enterprise_ai_platform.core.database import Base

if TYPE_CHECKING:
    from enterprise_ai_platform.auth.models import User


class Conversation(Base):
    """
    Independent dialogue session owned by an authenticated platform principal.
    """

    __tablename__ = "conversations"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'archived')", name="chk_conversations_status"),
        CheckConstraint(
            "generation_status IN ('idle', 'generating')",
            name="chk_conversations_generation_status",
        ),
        CheckConstraint(
            "title_source IN ('default', 'generated', 'user')",
            name="chk_conversations_title_source",
        ),
        CheckConstraint("next_sequence_number >= 1", name="chk_conversations_next_seq"),
        CheckConstraint(
            "(generation_status = 'idle' AND active_generation_message_id IS NULL) OR "
            "(generation_status = 'generating' AND active_generation_message_id IS NOT NULL)",
            name="chk_conversations_generation_ownership",
        ),
        UniqueConstraint("id", "user_id", name="uq_conversations_id_user"),
        ForeignKeyConstraint(
            ["active_generation_message_id", "id"],
            ["messages.id", "messages.conversation_id"],
            name="fk_conversations_active_generation_msg",
            ondelete="SET NULL",
            deferrable=True,
            initially="DEFERRED",
        ),
        Index(
            "idx_conversations_user_active",
            "user_id",
            text("is_pinned DESC"),
            text("last_message_at DESC NULLS LAST"),
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("idx_conversations_user_id", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="New Conversation",
        server_default="New Conversation",
    )
    title_source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="default",
        server_default="default",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        server_default="active",
    )
    is_pinned: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    last_message_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
    next_sequence_number: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=1,
        server_default="1",
    )
    generation_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="idle",
        server_default="idle",
    )
    active_generation_message_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.clock_timestamp(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.clock_timestamp(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )

    # Relationships
    user: Mapped[User] = relationship("User", foreign_keys=[user_id])
    messages: Mapped[list[Message]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        foreign_keys="[Message.conversation_id]",
        order_by="Message.sequence_number.asc()",
    )
    summaries: Mapped[list[ConversationSummary]] = relationship(
        "ConversationSummary",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ConversationSummary.version.asc()",
    )
    active_generation_message: Mapped[Message | None] = relationship(
        "Message",
        foreign_keys=[active_generation_message_id, id],
        primaryjoin="and_(Conversation.active_generation_message_id == Message.id, "
        "Conversation.id == Message.conversation_id)",
        post_update=True,
    )


class Message(Base):
    """
    Individual dialogue turn in a conversation.
    """

    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'assistant', 'system')",
            name="chk_messages_role",
        ),
        CheckConstraint(
            "status IN ('pending', 'streaming', 'completed', 'failed', 'interrupted')",
            name="chk_messages_status",
        ),
        CheckConstraint("sequence_number >= 1", name="chk_messages_sequence"),
        CheckConstraint(
            "client_message_id IS NULL OR role = 'user'",
            name="chk_messages_client_id_role",
        ),
        UniqueConstraint(
            "conversation_id",
            "sequence_number",
            name="uq_messages_conversation_sequence",
        ),
        UniqueConstraint(
            "id",
            "conversation_id",
            name="uq_messages_id_conversation",
        ),
        Index(
            "uq_messages_conversation_client_msg_id",
            "conversation_id",
            "client_message_id",
            unique=True,
            postgresql_where=text("client_message_id IS NOT NULL AND role = 'user'"),
        ),
        Index(
            "idx_messages_conv_status_created",
            "conversation_id",
            "status",
            "created_at",
        ),
        Index(
            "idx_messages_parent_id",
            "parent_message_id",
            postgresql_where=text("parent_message_id IS NOT NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    sequence_number: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        server_default="",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
    )
    client_message_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True,
    )
    parent_message_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
    )
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.clock_timestamp(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )

    # Relationships
    conversation: Mapped[Conversation] = relationship(
        "Conversation",
        back_populates="messages",
        foreign_keys=[conversation_id],
    )
    parent_message: Mapped[Message | None] = relationship(
        "Message",
        remote_side=[id],
        foreign_keys=[parent_message_id],
    )
    feedback: Mapped[list[MessageFeedback]] = relationship(
        "MessageFeedback",
        back_populates="message",
        cascade="all, delete-orphan",
        foreign_keys="[MessageFeedback.message_id, MessageFeedback.conversation_id]",
    )


class MessageFeedback(Base):
    """
    User rating and optional commentary on completed assistant messages.
    """

    __tablename__ = "message_feedback"
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="chk_feedback_rating"),
        UniqueConstraint("message_id", "user_id", name="uq_feedback_message_user"),
        ForeignKeyConstraint(
            ["message_id", "conversation_id"],
            ["messages.id", "messages.conversation_id"],
            name="fk_feedback_message_owner",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["conversation_id", "user_id"],
            ["conversations.id", "conversations.user_id"],
            name="fk_feedback_user_owner",
            ondelete="CASCADE",
        ),
        Index("idx_feedback_conversation_id", "conversation_id"),
        Index("idx_feedback_user_id", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
    )
    rating: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
    )
    comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.clock_timestamp(),
    )

    # Relationships
    message: Mapped[Message] = relationship(
        "Message",
        back_populates="feedback",
        foreign_keys=[message_id, conversation_id],
    )
    user: Mapped[User] = relationship(
        "User",
        primaryjoin="MessageFeedback.user_id == User.id",
        foreign_keys=[user_id],
    )


class ConversationSummary(Base):
    """
    Periodic condensation of historical dialogue turns.
    """

    __tablename__ = "conversation_summaries"
    __table_args__ = (
        CheckConstraint("version >= 1", name="chk_summaries_version"),
        CheckConstraint(
            "summarized_through_sequence >= 1",
            name="chk_summaries_through_seq",
        ),
        UniqueConstraint(
            "conversation_id",
            "version",
            name="uq_summaries_conversation_version",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
    summarized_through_sequence: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.clock_timestamp(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.clock_timestamp(),
    )

    # Relationships
    conversation: Mapped[Conversation] = relationship(
        "Conversation",
        back_populates="summaries",
    )
