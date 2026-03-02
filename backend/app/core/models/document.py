"""Document ORM model — uploaded files tracked for RAG pipeline."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DocumentStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    ready = "ready"
    error = "error"


class DocumentAccessLevel(str, enum.Enum):
    public = "public"
    private = "private"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(127), nullable=False)

    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="documentstatus"),
        nullable=False,
        default=DocumentStatus.pending,
    )
    error_message: Mapped[str | None] = mapped_column(Text)

    access_level: Mapped[DocumentAccessLevel] = mapped_column(
        Enum(DocumentAccessLevel, name="documentaccesslevel"),
        nullable=False,
        default=DocumentAccessLevel.private,
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
