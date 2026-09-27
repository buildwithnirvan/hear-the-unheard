"""
Document shapes for model_versions, datasets, samples, training_runs,
conversations, messages, and audit_logs collections. §20/§21/§23/§27.
"""
import enum
import uuid
from datetime import datetime, timezone


def gen_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ModelStatus(str, enum.Enum):
    TRAINING = "training"
    EVALUATING = "evaluating"
    READY = "ready"
    ACTIVE = "active"
    RETIRED = "retired"
    FAILED = "failed"


class SampleStatus(str, enum.Enum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class TrainingRunStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class InputModality(str, enum.Enum):
    ISL = "isl"
    SPEECH = "speech"
    TEXT = "text"
    FINGERSPELLING = "fingerspelling"


def new_model_version_document(
    version_tag: str,
    vocabulary_version: int,
    dataset_version: str,
    training_date: datetime | None = None,
    accuracy: float | None = None,
    validation_accuracy: float | None = None,
    f1_score: float | None = None,
    confusion_matrix: dict | None = None,
    inference_latency_ms: float | None = None,
    status: ModelStatus = ModelStatus.TRAINING,
    artifact_path: str | None = None,
    notes: str | None = None,
) -> dict:
    """
    §20. No row from this builder should ever be called with fabricated
    metrics — accuracy/f1/etc. must come from a real evaluation run (see
    ml/training/train_pose_classifier.py's model card), never hardcoded.
    """
    return {
        "_id": gen_uuid(),
        "version_tag": version_tag,
        "vocabulary_version": vocabulary_version,
        "dataset_version": dataset_version,
        "training_date": training_date,
        "accuracy": accuracy,
        "validation_accuracy": validation_accuracy,
        "f1_score": f1_score,
        "confusion_matrix": confusion_matrix,
        "inference_latency_ms": inference_latency_ms,
        "status": status.value,
        "artifact_path": artifact_path,
        "notes": notes,
        "created_at": utcnow(),
    }


def new_dataset_document(name: str, source: str, version: str, license: str | None = None, sample_count: int = 0) -> dict:
    return {
        "_id": gen_uuid(),
        "name": name,
        "source": source,
        "license": license,
        "version": version,
        "sample_count": sample_count,
        "created_at": utcnow(),
    }


def new_sample_document(
    dataset_id: str, sign_id: str, file_path: str, landmark_path: str | None = None, submitted_by: str | None = None
) -> dict:
    return {
        "_id": gen_uuid(),
        "dataset_id": dataset_id,
        "sign_id": sign_id,
        "file_path": file_path,
        "landmark_path": landmark_path,
        "status": SampleStatus.PENDING_REVIEW.value,
        "submitted_by": submitted_by,
        "created_at": utcnow(),
    }


def new_training_run_document(dataset_id: str, started_by: str, hyperparameters: dict | None = None) -> dict:
    return {
        "_id": gen_uuid(),
        "dataset_id": dataset_id,
        "started_by": started_by,
        "status": TrainingRunStatus.QUEUED.value,
        "hyperparameters": hyperparameters,
        "result_model_version_id": None,
        "log_path": None,
        "started_at": utcnow(),
        "completed_at": None,
    }


def new_conversation_document(user_id: str, title: str | None = None) -> dict:
    return {"_id": gen_uuid(), "user_id": user_id, "title": title, "created_at": utcnow()}


def new_message_document(
    conversation_id: str,
    input_modality: InputModality,
    translated_text: str,
    recognized_tokens: list[str] | None = None,
    confidence: float | None = None,
) -> dict:
    return {
        "_id": gen_uuid(),
        "conversation_id": conversation_id,
        "input_modality": input_modality.value,
        "recognized_tokens": recognized_tokens,
        "translated_text": translated_text,
        "confidence": confidence,
        "created_at": utcnow(),
    }


def new_audit_log_document(actor_user_id: str, action: str, target_type: str | None = None, target_id: str | None = None, detail: dict | None = None) -> dict:
    return {
        "_id": gen_uuid(),
        "actor_user_id": actor_user_id,
        "action": action,
        "target_type": target_type,
        "target_id": target_id,
        "detail": detail,
        "created_at": utcnow(),
    }
