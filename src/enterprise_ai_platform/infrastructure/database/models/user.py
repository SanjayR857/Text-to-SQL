"""
User model representing the pre-existing external platform identity table.
"""
import uuid

from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column

from enterprise_ai_platform.infrastructure.database.base import Base


class User(Base):
    """
    Representation of the existing platform `users` table.

    The Chat / Conversation Management module references this table via foreign keys
    (e.g., conversations.user_id, message_feedback.user_id) but does not own,
    create, or drop this table.
    """

    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        comment="External platform principal primary key",
    )
