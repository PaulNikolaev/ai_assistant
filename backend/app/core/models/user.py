"""User ORM model."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserRole(str, enum.Enum):
    superadmin = "superadmin"
    admin = "admin"
    user = "user"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    patronymic: Mapped[str | None] = mapped_column(String(100))
    position: Mapped[str | None] = mapped_column(String(255))

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="userrole"),
        nullable=False,
        default=UserRole.user,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
