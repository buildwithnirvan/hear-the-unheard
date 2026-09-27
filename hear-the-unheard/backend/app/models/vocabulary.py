"""
Document shape for the `signs` collection (§11 ISL vocabulary database).
Plain dicts in MongoDB — these are builder helpers + the enum vocabulary,
not an ORM.
"""
import enum
import uuid
from datetime import datetime, timezone


def gen_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SignType(str, enum.Enum):
    STATIC = "static"
    DYNAMIC = "dynamic"


class SignCategory(str, enum.Enum):
    GREETING = "greeting"
    NOUN = "noun"
    PRONOUN = "pronoun"
    VERB = "verb"
    ADJECTIVE = "adjective"
    QUESTION = "question"
    NUMBER = "number"
    ALPHABET = "alphabet"
    EMERGENCY = "emergency"
    EDUCATION = "education"
    MEDICAL = "medical"
    TRAVEL = "travel"
    WORKPLACE = "workplace"
    GOVERNMENT = "government"
    FAMILY = "family"
    TIME_DATE = "time_date"
    CONVERSATIONAL_PHRASE = "conversational_phrase"


def new_sign_document(
    sign_id: str,
    gloss: str,
    category: SignCategory,
    sign_type: SignType,
    english_meaning: str,
    required_hands: str = "single",
    hindi_meaning: str | None = None,
    kannada_meaning: str | None = None,
    description: str | None = None,
    example_sentences: list[str] | None = None,
    dataset_references: list[str] | None = None,
    model_label: int | None = None,
    confidence_threshold: float = 0.75,
) -> dict:
    """
    One `signs` document. `model_label` stays None until a real trained
    model actually supports this sign — see §33, never set this just
    because the sign is documented.
    """
    now = utcnow()
    return {
        "_id": gen_uuid(),
        "sign_id": sign_id,
        "gloss": gloss,
        "category": category.value,
        "sign_type": sign_type.value,
        "english_meaning": english_meaning,
        "hindi_meaning": hindi_meaning,
        "kannada_meaning": kannada_meaning,
        "description": description,
        "required_hands": required_hands,
        "example_sentences": example_sentences,
        "dataset_references": dataset_references,
        "model_label": model_label,
        "confidence_threshold": confidence_threshold,
        "is_trainable": True,
        "version": 1,
        "created_at": now,
        "updated_at": now,
    }
