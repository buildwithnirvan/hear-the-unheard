import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo.database import Database

from app.database.mongo import get_db
from app.models.vocabulary import SignCategory

router = APIRouter(prefix="/vocabulary", tags=["vocabulary"])


def _serialize(doc: dict) -> dict:
    return {
        "sign_id": doc["sign_id"],
        "gloss": doc["gloss"],
        "category": doc["category"],
        "type": doc["sign_type"],
        "english": doc["english_meaning"],
        "hindi": doc.get("hindi_meaning"),
        "kannada": doc.get("kannada_meaning"),
        "recognizable": doc.get("model_label") is not None,
    }


@router.get("")
def list_vocabulary(
    category: Optional[SignCategory] = None,
    recognizable_only: bool = False,
    search: Optional[str] = Query(None, description="Substring match on gloss or English meaning"),
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: Database = Depends(get_db),
):
    query: dict = {}
    if category:
        query["category"] = category.value
    if recognizable_only:
        query["model_label"] = {"$ne": None}
    if search:
        pattern = re.compile(re.escape(search), re.IGNORECASE)
        query["$or"] = [{"gloss": pattern}, {"english_meaning": pattern}]

    total = db.signs.count_documents(query)
    cursor = db.signs.find(query).sort("gloss", 1).skip(offset).limit(limit)
    rows = list(cursor)

    return {"total": total, "count": len(rows), "items": [_serialize(r) for r in rows]}


@router.get("/{sign_id}")
def get_sign(sign_id: str, db: Database = Depends(get_db)):
    doc = db.signs.find_one({"sign_id": sign_id})
    if not doc:
        raise HTTPException(status_code=404, detail=f"No sign with sign_id={sign_id}")
    result = _serialize(doc)
    result.update(
        {
            "description": doc.get("description"),
            "required_hands": doc.get("required_hands"),
            "example_sentences": doc.get("example_sentences"),
            "confidence_threshold": doc.get("confidence_threshold"),
        }
    )
    return result


@router.get("/stats/summary")
def vocabulary_stats(db: Database = Depends(get_db)):
    """
    Honest coverage reporting per §33: never claim broader ISL support than
    what is actually trained. Counts real documents, nothing hardcoded.
    """
    total = db.signs.count_documents({})
    recognizable = db.signs.count_documents({"model_label": {"$ne": None}})
    by_category = {cat.value: db.signs.count_documents({"category": cat.value}) for cat in SignCategory}

    return {
        "total_vocabulary_entries": total,
        "recognizable_by_current_model": recognizable,
        "unrecognizable_documented_only": total - recognizable,
        "by_category": by_category,
        "note": (
            "recognizable_by_current_model reflects signs with a trained "
            "model_label. A high total_vocabulary_entries count does not by "
            "itself imply recognition coverage."
        ),
    }
