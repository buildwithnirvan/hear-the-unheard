"""
mongo.py

MongoDB-only data layer (no SQL anywhere in this project — see
docs/STATUS.md for the reasoning). One MongoClient per process, reused
across requests; get_db() is the FastAPI dependency every endpoint uses
to reach it.

Documents use our own string ids (uuid4, same scheme as before) stored in
the real MongoDB `_id` field, rather than letting MongoDB generate
ObjectIds. Reason: ObjectId isn't JSON-serializable without a custom
encoder, and ids already appear in API responses (sign_id, user id in
JWTs, etc.) — keeping them as plain strings throughout avoids a whole
class of serialization bugs at every API boundary, at the cost of losing
ObjectId's embedded-timestamp property (which nothing here relied on).
"""
from __future__ import annotations

from pymongo import MongoClient
from pymongo.database import Database

from app.core.config import get_settings

settings = get_settings()

_client: MongoClient | None = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(settings.mongodb_url)
    return _client


def get_database() -> Database:
    return get_client()[settings.mongodb_db_name]


def get_db() -> Database:
    """FastAPI dependency — Depends(get_db) in every endpoint that touches data."""
    return get_database()


def ensure_indexes() -> None:
    """
    Called once at app startup (see app/main.py). MongoDB doesn't enforce
    schema or foreign keys, so these unique/lookup indexes are the actual
    substitute for what SQL UNIQUE constraints and foreign keys used to
    give us — without them, e.g. two users could register the same email.
    """
    db = get_database()
    db.users.create_index("email", unique=True)
    db.signs.create_index("sign_id", unique=True)
    db.signs.create_index("gloss")
    db.signs.create_index("category")
    db.signs.create_index("model_label")
    db.model_versions.create_index("version_tag", unique=True)
    db.model_versions.create_index("status")
    db.samples.create_index("dataset_id")
    db.samples.create_index("sign_id")
    db.conversations.create_index("user_id")
    db.messages.create_index("conversation_id")
    db.audit_logs.create_index("actor_user_id")
