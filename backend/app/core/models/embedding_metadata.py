"""EmbeddingMetadata ORM model — tracks Qdrant chunks per document."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class EmbeddingMetadata(Base):
    __tablename__ = "embedding_metadata"
    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_embedding_metadata_document_chunk"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer)
    qdrant_point_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), unique=True
    )
    chunk_text: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
