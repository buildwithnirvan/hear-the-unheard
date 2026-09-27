"""
recognize_ws.py

The real-time path for Phase 4 (continuous recognition), §15 of the spec.
A client streams JPEG-encoded frames over a WebSocket; this endpoint:

  frame bytes -> decode -> MediaPipe Pose -> normalized feature vector
    -> SignSegmenter (detects when a sign starts/ends)
    -> on a closed window: ISLClassifier.predict_from_sequence()
    -> PredictionDebouncer (suppress repeat-emitting a held sign)
    -> send a JSON status message back to the client every frame, and a
       JSON recognition message whenever a sign is actually recognized

This reuses the exact same LandmarkExtractor normalization, SignSegmenter,
and ISLClassifier already verified in ml/preprocessing/tests and via the
/api/v1/recognize/video endpoint — no separate/duplicated logic that could
drift out of sync with what was actually tested.

Protocol (client -> server): binary WebSocket messages, each one JPEG-
encoded frame (what a browser's canvas.toBlob('image/jpeg') produces).

Protocol (server -> client): JSON text messages —
  {"type": "status", "hands_present": bool, "pose_present": bool,
   "frame_index": int}
  {"type": "recognition", "gloss": str, "confidence": float,
   "window_frames": int}
  {"type": "error", "detail": str}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

ML_ROOT = Path(__file__).parent.parent.parent.parent / "ml"
sys.path.insert(0, str(ML_ROOT / "preprocessing"))
from landmark_extractor import LandmarkExtractor, UPPER_BODY_POSE_INDICES  # noqa: E402
from sign_segmenter import SignSegmenter, SegmentationConfig, PredictionDebouncer  # noqa: E402

from app.ml.vision.isl_classifier import get_classifier  # noqa: E402

router = APIRouter()

POSE_FEATURE_DIM = len(UPPER_BODY_POSE_INDICES) * 4

# Index of the wrist landmarks within the 60-dim pose-only feature vector.
# UPPER_BODY_POSE_INDICES = [0, 11,12, 13,14, 15,16, 17,18, 19,20, 21,22, 23,24]
#                                              ^left wrist=15 is position 5
#                                                  ^right wrist=16 is position 6
_LEFT_WRIST_POS = UPPER_BODY_POSE_INDICES.index(15)
_RIGHT_WRIST_POS = UPPER_BODY_POSE_INDICES.index(16)


def _pose_centroid(feature_vec: np.ndarray) -> np.ndarray:
    """
    Centroid function for SignSegmenter matching the pose-only 60-dim
    feature layout this WebSocket path uses (NOT the 188-dim hand-based
    layout SignSegmenter defaults to — see its constructor docstring).
    Uses the midpoint of both wrists as a proxy for "where the signing
    motion is happening", since we don't have hand landmarks here.
    """
    pose = feature_vec.reshape(len(UPPER_BODY_POSE_INDICES), 4)
    left_wrist_xy = pose[_LEFT_WRIST_POS, :2]
    right_wrist_xy = pose[_RIGHT_WRIST_POS, :2]
    return (left_wrist_xy + right_wrist_xy) / 2.0


def _pose_feature_vector(pose_model, frame_bgr: np.ndarray) -> tuple[np.ndarray, bool]:
    """Returns (feature_vector, pose_present). Mirrors extract_dataset_landmarks.py exactly."""
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    result = pose_model.process(rgb)
    if result.pose_landmarks is None:
        return np.zeros(POSE_FEATURE_DIM, dtype=np.float32), False
    pose = np.array(
        [[lm.x, lm.y, lm.z, lm.visibility] for lm in result.pose_landmarks.landmark],
        dtype=np.float32,
    )
    return LandmarkExtractor._normalize_pose_subset(pose).flatten(), True


@router.websocket("/ws/recognize")
async def recognize_stream(websocket: WebSocket):
    await websocket.accept()

    classifier = get_classifier()
    pose_model = mp.solutions.pose.Pose(
        static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5
    )
    segmenter = SignSegmenter(SegmentationConfig(), centroid_fn=_pose_centroid)
    debouncer = PredictionDebouncer()
    frame_index = 0
    went_idle_since_last = True  # starts idle

    try:
        while True:
            message = await websocket.receive()

            if message["type"] == "websocket.disconnect":
                # The low-level receive() used here (needed to accept both
                # binary frames and text control messages on one socket)
                # does NOT auto-raise WebSocketDisconnect the way
                # receive_bytes()/receive_json() do — it just returns this
                # as a regular message. Calling receive() again after this
                # is explicitly invalid in Starlette and raises a
                # RuntimeError (hit this for real — see docs/STATUS.md).
                # Must break out here ourselves.
                break

            if message.get("bytes") is not None:
                data = message["bytes"]
                frame_index += 1

                np_arr = np.frombuffer(data, dtype=np.uint8)
                frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                if frame is None:
                    await websocket.send_json({"type": "error", "detail": "Could not decode frame"})
                    continue

                feature_vec, pose_present = _pose_feature_vector(pose_model, frame)

                await websocket.send_json(
                    {
                        "type": "status",
                        "hands_present": None,  # not tracked in pose-only mode — see model card
                        "pose_present": pose_present,
                        "frame_index": frame_index,
                    }
                )

                if not pose_present:
                    went_idle_since_last = True

                window = segmenter.push(feature_vec, hands_present=pose_present)
                if window is not None:
                    await _classify_and_emit(websocket, classifier, debouncer, window, went_idle_since_last)
                    went_idle_since_last = False

            elif message.get("text") is not None:
                # Explicit end-of-stream control message from the client
                # (see tests/test_ws_client.py / frontend integration).
                # This is the ONLY reliable way to deliver a final
                # recognition for a sign the stream ends in the middle of
                # — sending it in response to WebSocketDisconnect doesn't
                # work, because by the time that exception fires the
                # client has already stopped listening and the message
                # would just be silently dropped. Verified by testing:
                # the disconnect-triggered version below looked like a
                # fix but delivered nothing; this explicit handshake
                # actually gets received.
                try:
                    payload = json.loads(message["text"])
                except (json.JSONDecodeError, TypeError):
                    payload = {}

                if payload.get("type") == "end_of_stream":
                    pending = segmenter.flush()
                    if pending is not None:
                        await _classify_and_emit(
                            websocket, classifier, debouncer, pending, went_idle_since_last,
                            flushed=True,
                        )
                    await websocket.send_json({"type": "stream_ended"})

    except WebSocketDisconnect:
        pass
    finally:
        pose_model.close()


async def _classify_and_emit(websocket, classifier, debouncer, window, went_idle_since_last, flushed=False):
    if not classifier.is_available:
        await websocket.send_json(
            {"type": "error", "detail": "No trained model loaded — see /api/v1/model/status"}
        )
        return
    sequence = np.stack(window.feature_vectors, axis=0)
    predictions = classifier.predict_from_sequence(sequence, top_k=1)
    if predictions:
        top = predictions[0]
        if debouncer.should_emit(top["gloss"], went_idle_since_last):
            msg = {
                "type": "recognition",
                "gloss": top["gloss"],
                "confidence": top["confidence"],
                "window_frames": window.length,
            }
            if flushed:
                msg["flushed_at_stream_end"] = True
            await websocket.send_json(msg)
