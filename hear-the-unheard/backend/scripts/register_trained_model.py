"""
Registers the trained pose classifier (Phase 3, v1) in the backend:
  1. Adds/updates `signs` documents for the 76 trained classes, setting
     model_label to match the classifier's real class index — so
     /api/v1/vocabulary honestly reflects what's recognizable.
  2. Creates a `datasets` document documenting the real source data.
  3. Creates a `model_versions` document with the REAL cross-validated
     metrics from train_pose_classifier.py's model card — never hardcoded.
  4. Activates that model version (retires any previously active one).

Run after ml/training/train_pose_classifier.py has produced
ml/models/pose_classifier_v1_model_card.json. Idempotent for the
vocabulary side (upserts by sign_id/gloss); each run creates a fresh
model_versions document, matching what a real new training run would do.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.mongo import get_database, ensure_indexes
from app.models.vocabulary import SignType, SignCategory, new_sign_document
from app.models.ml_ops import ModelStatus, new_dataset_document, new_model_version_document

MODEL_CARD_PATH = Path(__file__).parent.parent.parent / "ml" / "models" / "pose_classifier_v1_model_card.json"

CATEGORY_MAP = {
    "afternoon": SignCategory.TIME_DATE, "evening": SignCategory.TIME_DATE,
    "morning": SignCategory.TIME_DATE, "night": SignCategory.TIME_DATE,
    "today": SignCategory.TIME_DATE, "tomorrow": SignCategory.TIME_DATE,
    "yesterday": SignCategory.TIME_DATE, "hour": SignCategory.TIME_DATE,
    "minute": SignCategory.TIME_DATE, "second": SignCategory.TIME_DATE,
    "week": SignCategory.TIME_DATE, "month": SignCategory.TIME_DATE,
    "year": SignCategory.TIME_DATE, "time": SignCategory.TIME_DATE,
    "monday": SignCategory.TIME_DATE, "tuesday": SignCategory.TIME_DATE,
    "wednesday": SignCategory.TIME_DATE, "thursday": SignCategory.TIME_DATE,
    "friday": SignCategory.TIME_DATE, "saturday": SignCategory.TIME_DATE,
    "sunday": SignCategory.TIME_DATE,
}
NOUN_CLASSES = {
    "animal", "bird", "cat", "cow", "dog", "fish", "horse", "mouse",
    "clothing", "dress", "hat", "pant", "pocket", "shirt", "shoes",
    "skirt", "suit", "t_shirt",
}


def category_for(class_name: str) -> SignCategory:
    if class_name in CATEGORY_MAP:
        return CATEGORY_MAP[class_name]
    if class_name in NOUN_CLASSES:
        return SignCategory.NOUN
    return SignCategory.ADJECTIVE


def run():
    if not MODEL_CARD_PATH.exists():
        print(f"ERROR: {MODEL_CARD_PATH} not found — run train_pose_classifier.py first.")
        sys.exit(1)

    card = json.loads(MODEL_CARD_PATH.read_text())
    classes = card["classes"]

    db = get_database()
    ensure_indexes()

    # 1. Dataset document — real provenance, not invented.
    dataset_doc = new_dataset_document(
        name="Kaggle ISL words with Landmarks (user-provided, pose-only extraction)",
        source=(
            "Kaggle: kaushikyh/indian-sign-language-words-with-landmarks "
            "(CC BY-SA 4.0), derived from INCLUDE (IIT Madras/AI4Bharat). "
            "Pose landmarks re-extracted locally with MediaPipe Pose "
            "(hand landmarks NOT used — see ml/preprocessing/"
            "extract_dataset_landmarks.py docstring for why)."
        ),
        license="CC BY-SA 4.0",
        version="v1",
        sample_count=card["num_samples"],
    )
    db.datasets.insert_one(dataset_doc)

    # 2. Vocabulary — add or update, don't duplicate.
    added, updated = 0, 0
    for class_idx, class_name in enumerate(classes):
        gloss = class_name.upper()
        existing = db.signs.find_one({"gloss": gloss})
        if existing:
            db.signs.update_one(
                {"_id": existing["_id"]},
                {"$set": {"model_label": class_idx, "confidence_threshold": 0.5}},
            )
            updated += 1
        else:
            sign_id = f"ISL_DATASET_{class_idx:03d}"
            doc = new_sign_document(
                sign_id=sign_id,
                gloss=gloss,
                category=category_for(class_name),
                sign_type=SignType.DYNAMIC,
                english_meaning=class_name.replace("_", " "),
                required_hands="single",
                model_label=class_idx,
                confidence_threshold=0.5,
                dataset_references=[dataset_doc["name"]],
            )
            db.signs.insert_one(doc)
            added += 1

    print(f"Vocabulary: added {added} new signs, updated {updated} existing signs with model_label")

    # 3. Model version — real metrics only, straight from the model card.
    db.model_versions.update_many({"status": ModelStatus.ACTIVE.value}, {"$set": {"status": ModelStatus.RETIRED.value}})

    model_doc = new_model_version_document(
        version_tag=card["version_tag"],
        vocabulary_version=1,
        dataset_version=dataset_doc["version"],
        training_date=datetime.now(timezone.utc),
        accuracy=card["cross_validated_accuracy"],
        validation_accuracy=card["cross_validated_accuracy"],  # CV accuracy IS the validation metric here
        f1_score=card["cross_validated_macro_f1"],
        confusion_matrix={"note": "see ml/models/pose_classifier_v1_model_card.json for full matrix"},
        status=ModelStatus.ACTIVE,
        artifact_path="ml/models/pose_classifier_v1.joblib",
        notes=(
            "Pose-only classifier (not hand-shape). "
            f"Trained on {card['num_samples']} samples across {card['num_classes']} classes. "
            "See model card for per-class accuracy and full limitations."
        ),
    )
    # version_tag has a unique index — if this exact tag was registered
    # before (e.g. re-running this script without retraining), replace it
    # rather than erroring, since that's clearly the intent of a rerun.
    db.model_versions.delete_many({"version_tag": model_doc["version_tag"]})
    db.model_versions.insert_one(model_doc)

    print(f"Registered and activated model version: {model_doc['version_tag']}")
    print(f"  accuracy={model_doc['accuracy']:.3f}  f1={model_doc['f1_score']:.3f}")


if __name__ == "__main__":
    run()
