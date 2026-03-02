"""ChatHistory ORM model — per-user dialogue log with feedback."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Enum, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ChatRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"


class ChatHistory(Base):
    __tablename__ = "chat_history"
    __table_args__ = (
        Index("ix_chat_history_user_id_created_at", "user_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[ChatRole] = mapped_column(
        Enum(ChatRole, name="chatrole"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    feedback_rating: Mapped[int | None] = mapped_column(Integer)
    feedback_comment: Mapped[str | None] = mapped_column(Text)
    prompt_variant: Mapped[str | None] = mapped_column(String(100))
    retrieval_score: Mapped[float | None] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
