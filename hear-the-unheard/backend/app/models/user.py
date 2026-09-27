"""
User document shape for the `users` collection. This is NOT an ORM model
— MongoDB documents are plain dicts; these are just the schema/validation
layer (Pydantic) used when building or reading a document, and the
uniqueness constraint lives in the real unique index on `email` (see
app/database/mongo.py:ensure_indexes), not in application code alone.
"""
import enum
import uuid
from datetime import datetime, timezone


def gen_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UserRole(str, enum.Enum):
    USER = "user"
    TRAINER_ADMIN = "trainer_admin"
    ADMINISTRATOR = "administrator"


def new_user_document(email: str, display_name: str, hashed_password: str) -> dict:
    """Builds a fresh `users` document ready to insert_one(). §22 auth."""
    now = utcnow()
    return {
        "_id": gen_uuid(),
        "email": email,
        "display_name": display_name,
        "hashed_password": hashed_password,
        "role": UserRole.USER.value,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
