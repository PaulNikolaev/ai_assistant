"""Factory-boy factories for creating test ORM objects without a database.

Usage:
    user = UserFactory()                  # User with role=user
    admin = AdminFactory(first_name="Jo") # override any field
    db.add(user); await db.commit()       # persist if needed
"""

import uuid
from datetime import datetime, timezone

import factory

from app.core.models.user import User, UserRole


class UserFactory(factory.Factory):
    class Meta:
        model = User

    id = factory.LazyFunction(uuid.uuid4)
    email = factory.Sequence(lambda n: f"user{n}@test.com")
    username = factory.Sequence(lambda n: f"user{n}")
    hashed_password = "$2b$12$fakehashfortest000000000000000000000000000000000000"
    first_name = "Test"
    last_name = "User"
    patronymic = None
    position = None
    role = UserRole.user
    is_active = True
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))


class AdminFactory(UserFactory):
    email = factory.Sequence(lambda n: f"admin{n}@test.com")
    username = factory.Sequence(lambda n: f"admin{n}")
    role = UserRole.admin


class SuperAdminFactory(UserFactory):
    email = factory.Sequence(lambda n: f"superadmin{n}@test.com")
    username = factory.Sequence(lambda n: f"superadmin{n}")
    role = UserRole.superadmin
