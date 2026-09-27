"""
landmark_extractor.py

Real, working computer-vision feature extraction for Hear the Unheard.

This module wraps MediaPipe's Hands + Pose solutions to turn a raw video
frame into a normalized numeric feature vector suitable for feeding into a
sign-recognition model (static classifier or temporal sequence model).

IMPORTANT ENGINEERING NOTE (read before touching model versions):
-------------------------------------------------------------------
MediaPipe's newer "Tasks" API (mediapipe.tasks.python.vision) requires
downloading .task model files at runtime from storage.googleapis.com.
In network-restricted environments (CI runners, sandboxed dev containers,
some enterprise networks) that host is not reachable and the Tasks API
cannot initialize.

mediapipe==0.10.13 is the last line that ships the classic
`mediapipe.solutions.hands` / `mediapipe.solutions.pose` API with the
underlying .tflite model weights *bundled inside the pip wheel itself*.
No network access is required at runtime. This is the version pinned in
requirements.txt for that reason. If you upgrade mediapipe, you must
either (a) vendor the .task model files into the repo yourself with a
verified checksum, or (b) keep a network path to storage.googleapis.com
available at deploy time. Do not silently switch APIs.

This module has been verified to actually load both models and run
inference (not just import cleanly) — see tests/test_landmark_extractor.py.
"""

from __future__ import annotations

import dataclasses
from typing import Optional

import numpy as np

try:
    import mediapipe as mp
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "mediapipe is required. Install with: pip install mediapipe==0.10.13"
    ) from e

# --- Landmark topology constants -------------------------------------------------
NUM_HAND_LANDMARKS = 21          # per hand, from MediaPipe Hands
NUM_HAND_DIMS = 3                # x, y, z per landmark
NUM_POSE_LANDMARKS = 33          # from MediaPipe Pose (full body)
NUM_POSE_DIMS = 4                # x, y, z, visibility

# Feature vector layout (single frame):
#   [left_hand(21*3)] [right_hand(21*3)] [pose_upper_body_subset(*4)]
# Missing hands/pose are zero-filled, with an explicit presence flag appended
# so the model can distinguish "hand at origin" from "hand not detected".
UPPER_BODY_POSE_INDICES = [
    0,   # nose
    11, 12,   # shoulders
    13, 14,   # elbows
    15, 16,   # wrists
    17, 18,   # pinky
    19, 20,   # index
    21, 22,   # thumb
    23, 24,   # hips (for torso scale reference)
]

FRAME_FEATURE_DIM = (
    NUM_HAND_LANDMARKS * NUM_HAND_DIMS * 2          # both hands
    + len(UPPER_BODY_POSE_INDICES) * NUM_POSE_DIMS  # upper-body pose subset
    + 2                                             # presence flags: [left_hand_present, right_hand_present]
)


@dataclasses.dataclass
class FrameLandmarks:
    """Raw, un-normalized landmarks extracted from a single frame."""
    left_hand: Optional[np.ndarray]   # (21, 3) or None
    right_hand: Optional[np.ndarray]  # (21, 3) or None
    pose: Optional[np.ndarray]        # (33, 4) or None
    handedness_confidence: dict       # {"Left": float, "Right": float}


class LandmarkExtractor:
    """
    Wraps MediaPipe Hands + Pose to produce per-frame landmark data and
    normalized feature vectors ready for a sequence model.

    Usage:
        extractor = LandmarkExtractor()
        raw = extractor.process_frame(bgr_frame)         # FrameLandmarks
        vec = extractor.to_feature_vector(raw)            # np.ndarray, shape (FRAME_FEATURE_DIM,)
        extractor.close()
    """

    def __init__(
        self,
        static_image_mode: bool = False,
        max_num_hands: int = 2,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        enable_pose: bool = True,
        enable_hands: bool = True,
    ):
        self._mp_hands = mp.solutions.hands
        self._mp_pose = mp.solutions.pose

        self.hands = (
            self._mp_hands.Hands(
                static_image_mode=static_image_mode,
                max_num_hands=max_num_hands,
                min_detection_confidence=min_detection_confidence,
                min_tracking_confidence=min_tracking_confidence,
            )
            if enable_hands
            else None
        )
        self.pose = (
            self._mp_pose.Pose(
                static_image_mode=static_image_mode,
                min_detection_confidence=min_detection_confidence,
                min_tracking_confidence=min_tracking_confidence,
            )
            if enable_pose
            else None
        )

    def process_frame(self, bgr_frame: np.ndarray) -> FrameLandmarks:
        """
        Run hand + pose detection on a single BGR frame (as returned by
        cv2.VideoCapture.read()).
        """
        import cv2  # local import keeps this module importable without cv2 for pure unit tests

        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False

        hands_result = self.hands.process(rgb) if self.hands is not None else None
        pose_result = self.pose.process(rgb) if self.pose is not None else None

        left_hand = right_hand = None
        handedness_confidence = {}

        if hands_result is not None and hands_result.multi_hand_landmarks and hands_result.multi_handedness:
            for lm_set, handedness in zip(
                hands_result.multi_hand_landmarks, hands_result.multi_handedness
            ):
                label = handedness.classification[0].label  # "Left" or "Right"
                score = handedness.classification[0].score
                handedness_confidence[label] = score
                coords = np.array(
                    [[lm.x, lm.y, lm.z] for lm in lm_set.landmark], dtype=np.float32
                )
                # NOTE: MediaPipe's handedness label is from the camera's
                # perspective (mirrored), which matches a front-facing
                # selfie camera — the common deployment case for this app.
                if label == "Left":
                    left_hand = coords
                else:
                    right_hand = coords

        pose_coords = None
        if pose_result is not None and pose_result.pose_landmarks:
            pose_coords = np.array(
                [
                    [lm.x, lm.y, lm.z, lm.visibility]
                    for lm in pose_result.pose_landmarks.landmark
                ],
                dtype=np.float32,
            )

        return FrameLandmarks(
            left_hand=left_hand,
            right_hand=right_hand,
            pose=pose_coords,
            handedness_confidence=handedness_confidence,
        )

    @staticmethod
    def _normalize_hand(hand: np.ndarray) -> np.ndarray:
        """
        Normalize a single hand's landmarks to be invariant to hand
        position in frame and to overall hand size:
          1. Translate so the wrist (landmark 0) is the origin.
          2. Scale so the distance from wrist to middle-finger MCP (landmark 9)
             is 1.0.
        This is what makes recognition robust to camera distance and where
        in the frame the signer's hands happen to be.
        """
        wrist = hand[0]
        translated = hand - wrist
        scale_ref = np.linalg.norm(translated[9])
        if scale_ref < 1e-6:
            scale_ref = 1.0
        return translated / scale_ref

    @staticmethod
    def _normalize_pose_subset(pose: np.ndarray) -> np.ndarray:
        """
        Normalize the upper-body pose subset relative to the shoulder
        midpoint and shoulder width, so results don't depend on how far
        the signer is standing from the camera.
        """
        subset = pose[UPPER_BODY_POSE_INDICES]
        left_shoulder, right_shoulder = pose[11][:3], pose[12][:3]
        center = (left_shoulder + right_shoulder) / 2.0
        shoulder_width = np.linalg.norm(left_shoulder - right_shoulder)
        if shoulder_width < 1e-6:
            shoulder_width = 1.0

        out = subset.copy()
        out[:, :3] = (out[:, :3] - center) / shoulder_width
        return out

    def to_feature_vector(self, frame_landmarks: FrameLandmarks) -> np.ndarray:
        """
        Convert FrameLandmarks into a fixed-length, normalized float32
        vector of shape (FRAME_FEATURE_DIM,). Missing hands/pose are
        zero-filled; presence is signaled by the trailing two flag values
        so the model can tell "absent" from "at the normalized origin".
        """
        left = (
            self._normalize_hand(frame_landmarks.left_hand).flatten()
            if frame_landmarks.left_hand is not None
            else np.zeros(NUM_HAND_LANDMARKS * NUM_HAND_DIMS, dtype=np.float32)
        )
        right = (
            self._normalize_hand(frame_landmarks.right_hand).flatten()
            if frame_landmarks.right_hand is not None
            else np.zeros(NUM_HAND_LANDMARKS * NUM_HAND_DIMS, dtype=np.float32)
        )
        pose = (
            self._normalize_pose_subset(frame_landmarks.pose).flatten()
            if frame_landmarks.pose is not None
            else np.zeros(len(UPPER_BODY_POSE_INDICES) * NUM_POSE_DIMS, dtype=np.float32)
        )
        presence = np.array(
            [
                1.0 if frame_landmarks.left_hand is not None else 0.0,
                1.0 if frame_landmarks.right_hand is not None else 0.0,
            ],
            dtype=np.float32,
        )

        vec = np.concatenate([left, right, pose, presence]).astype(np.float32)
        assert vec.shape[0] == FRAME_FEATURE_DIM, (
            f"feature vector length mismatch: {vec.shape[0]} != {FRAME_FEATURE_DIM}"
        )
        return vec

    def close(self):
        if self.hands is not None:
            self.hands.close()
        if self.pose is not None:
            self.pose.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
