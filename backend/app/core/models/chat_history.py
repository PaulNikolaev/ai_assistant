"""ChatHistory ORM model — per-user dialogue log with feedback."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Double, Enum, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ChatRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"


class ChatHistory(Base):
    __tablename__ = "chat_history"
    __table_args__ = (
        Index("ix_chat_history_user_id_session_id", "user_id", "session_id"),
        Index("ix_chat_history_user_id_created_at", "user_id", "created_at"),
        CheckConstraint(
            "feedback_rating IS NULL OR (feedback_rating >= 1 AND feedback_rating <= 5)",
            name="ck_chat_history_feedback_rating_range",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), index=True
    )
    role: Mapped[ChatRole] = mapped_column(
        Enum(ChatRole, name="chatrole"),
    )
    content: Mapped[str] = mapped_column(Text)

    feedback_rating: Mapped[int | None] = mapped_column(Integer)
    feedback_comment: Mapped[str | None] = mapped_column(Text)
    prompt_variant: Mapped[str | None] = mapped_column(String(100))
    retrieval_score: Mapped[float | None] = mapped_column(Double)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
