import shutil
import sys
import tempfile
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile

ML_ROOT = Path(__file__).parent.parent.parent.parent.parent / "ml"
sys.path.insert(0, str(ML_ROOT / "preprocessing"))
from landmark_extractor import LandmarkExtractor  # noqa: E402
from app.ml.vision.isl_classifier import get_classifier  # noqa: E402

router = APIRouter(prefix="/recognize", tags=["recognize"])


@router.post("/video")
async def recognize_video(file: UploadFile = File(...)):
    """
    Real inference: accepts an uploaded video clip of one ISL sign,
    extracts pose landmarks with the same pipeline used for training, and
    returns the trained model's actual top-3 predictions with real
    confidence scores.

    If no model is loaded, this returns isl_recognition_available: false
    rather than a fabricated prediction — see /api/v1/model/status for
    the same honesty contract.
    """
    classifier = get_classifier()
    if not classifier.is_available:
        return {
            "isl_recognition_available": False,
            "reason": "No trained model is loaded. See /api/v1/model/status.",
        }

    suffix = Path(file.filename).suffix or ".mp4"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        pose_model = mp.solutions.pose.Pose(
            static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5
        )
        cap = cv2.VideoCapture(tmp_path)
        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="Could not open uploaded video file")

        frames = []
        frame_count = 0
        pose_detected_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame_count += 1
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = pose_model.process(rgb)
            if result.pose_landmarks is None:
                frames.append(np.zeros(15 * 4, dtype=np.float32))
                continue
            pose_detected_count += 1
            pose = np.array(
                [[lm.x, lm.y, lm.z, lm.visibility] for lm in result.pose_landmarks.landmark],
                dtype=np.float32,
            )
            frames.append(LandmarkExtractor._normalize_pose_subset(pose).flatten())

        cap.release()
        pose_model.close()

        if frame_count == 0:
            raise HTTPException(status_code=400, detail="Uploaded file contained no readable frames")

        sequence = np.stack(frames, axis=0)
        predictions = classifier.predict_from_sequence(sequence, top_k=3)

        return {
            "isl_recognition_available": True,
            "frames_processed": frame_count,
            "pose_detection_rate": round(pose_detected_count / frame_count, 3),
            "predictions": predictions,
            "note": (
                "Pose-only model — recognizes gross arm/body movement, not "
                "hand shape. See /api/v1/model/status and the model card "
                "for accuracy by class."
            ),
        }
    finally:
        Path(tmp_path).unlink(missing_ok=True)
