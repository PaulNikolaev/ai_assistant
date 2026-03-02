"""LlmProviderKey ORM model — encrypted API keys for LLM providers."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LlmProviderKey(Base):
    __tablename__ = "llm_provider_keys"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    key_encrypted: Mapped[str] = mapped_column(Text, nullable=False)

    label: Mapped[str | None] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
