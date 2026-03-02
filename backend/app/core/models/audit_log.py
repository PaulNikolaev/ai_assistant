"""AuditLog ORM model — immutable record of user actions."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSON, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_user_id_created_at", "user_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(100))
    resource_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))

    ip_address: Mapped[str | None] = mapped_column(String(45))
    details: Mapped[dict | None] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
