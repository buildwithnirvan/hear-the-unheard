from fastapi import APIRouter, Depends
from pymongo.database import Database

from app.database.mongo import get_db
from app.models.ml_ops import ModelStatus

router = APIRouter(prefix="/model", tags=["model"])


@router.get("/status")
def model_status(db: Database = Depends(get_db)):
    """
    §20 model management, §32 "do not fake predictions". If no model has
    ever been trained and activated, this says so plainly instead of a
    client silently getting empty/fake recognition results.
    """
    active = db.model_versions.find_one(
        {"status": ModelStatus.ACTIVE.value}, sort=[("training_date", -1)]
    )

    if active is None:
        return {
            "isl_recognition_available": False,
            "reason": (
                "No ISL recognition model has been trained and activated yet. "
                "The computer-vision pipeline (landmark extraction, sign "
                "segmentation) is implemented and running, but sign->label "
                "classification requires a trained model built from a real, "
                "licensed ISL dataset. See ml/training/README.md."
            ),
            "active_model": None,
        }

    return {
        "isl_recognition_available": True,
        "active_model": {
            "version_tag": active["version_tag"],
            "vocabulary_version": active["vocabulary_version"],
            "dataset_version": active["dataset_version"],
            "accuracy": active.get("accuracy"),
            "validation_accuracy": active.get("validation_accuracy"),
            "f1_score": active.get("f1_score"),
            "inference_latency_ms": active.get("inference_latency_ms"),
            "training_date": active["training_date"].isoformat() if active.get("training_date") else None,
        },
    }
