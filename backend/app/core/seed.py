"""Database seeding utilities.

Provides seed_superadmin() to ensure the initial superadmin account
exists at application startup (development only).
"""

import asyncio
import uuid

import bcrypt
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.models.user import User, UserRole

logger = structlog.get_logger(__name__)


async def seed_superadmin(db: AsyncSession) -> None:
    """Upsert the superadmin user defined in settings.

    - Creates the user if it does not exist.
    - Restores the superadmin role if the existing account was downgraded.
    - No-ops if the account already has the superadmin role.
    """
    result = await db.execute(
        select(User).where(User.email == settings.SUPERADMIN_EMAIL)
    )
    user = result.scalar_one_or_none()

    try:
        if user is None:
            hashed_password = await asyncio.to_thread(
                lambda: bcrypt.hashpw(
                    settings.SUPERADMIN_PASSWORD.encode(), bcrypt.gensalt()
                ).decode()
            )
            db.add(
                User(
                    id=uuid.uuid4(),
                    email=settings.SUPERADMIN_EMAIL,
                    username="superadmin",
                    hashed_password=hashed_password,
                    role=UserRole.superadmin,
                    is_active=True,
                )
            )
            await db.commit()
            logger.info("superadmin created", email=settings.SUPERADMIN_EMAIL)
        elif user.role != UserRole.superadmin:
            user.role = UserRole.superadmin
            await db.commit()
            logger.info("superadmin role restored", email=settings.SUPERADMIN_EMAIL)
        else:
            logger.debug("superadmin already exists", email=settings.SUPERADMIN_EMAIL)
    except Exception:
        await db.rollback()
        logger.exception("failed to seed superadmin", email=settings.SUPERADMIN_EMAIL)
        raise
