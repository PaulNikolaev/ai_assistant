"""SystemSettings ORM model — singleton row with runtime LLM/UI configuration."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SystemSettings(Base):
    __tablename__ = "system_settings"
    __table_args__ = (
        CheckConstraint("id = 1", name="ck_system_settings_singleton"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)

    llm_provider: Mapped[str] = mapped_column(String(50))
    llm_model: Mapped[str] = mapped_column(String(100))

    max_tokens: Mapped[int] = mapped_column(Integer, default=2048)
    temperature: Mapped[float] = mapped_column(Float, default=0.7)
    retrieval_top_k: Mapped[int] = mapped_column(Integer, default=5)

    welcome_message: Mapped[str | None] = mapped_column(Text)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
