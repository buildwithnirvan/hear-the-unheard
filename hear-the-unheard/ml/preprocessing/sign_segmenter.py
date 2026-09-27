"""
sign_segmenter.py

Temporal segmentation of a continuous landmark stream into discrete sign
"windows", plus prediction stabilization (debounce / voting) so that a
held sign doesn't get reported N times just because it was held for N
frames.

This module operates purely on landmark geometry (velocity, presence) and
does NOT require a trained sign-recognition model — it is real, working
logic today, independent of Phase 3 (model training). It is the piece
described in your spec §7 (segmentation) and §8 (stability).

Design:
  - Track per-frame hand velocity (Euclidean distance between consecutive
    normalized hand-landmark centroids).
  - A frame is "moving" if velocity exceeds a threshold, "idle" otherwise.
  - A sign window is: idle -> moving -> idle (rest position brackets a sign),
    OR — for signs held statically — a run of low-velocity frames with
    hands present, following a rest-then-appear transition.
  - Debounce: once a prediction is emitted for a window, the same label is
    suppressed until either (a) hands return to idle/rest, or (b) N frames
    of a *different* label are seen, so intentional repetition still works.
"""
from __future__ import annotations

import collections
import dataclasses
from enum import Enum
from typing import Deque, List, Optional

import numpy as np


class HandState(Enum):
    IDLE = "idle"          # no hands present / hands at rest
    MOVING = "moving"      # hand velocity above threshold
    HOLDING = "holding"    # hands present, low velocity (static sign being held)


@dataclasses.dataclass
class SegmentationConfig:
    velocity_threshold: float = 0.15       # normalized units/frame; tune against real footage
    idle_frames_to_close_window: int = 8   # consecutive idle frames that end a sign window
    min_window_frames: int = 4             # shorter than this is treated as noise, not a sign
    max_window_frames: int = 90            # safety cap (~3s at 30fps) to force-close a stuck window
    velocity_smoothing: int = 3            # moving-average window over raw velocity


@dataclasses.dataclass
class SignWindow:
    """A closed span of frames believed to contain exactly one sign."""
    start_frame: int
    end_frame: int
    feature_vectors: List[np.ndarray]

    @property
    def length(self) -> int:
        return len(self.feature_vectors)


class SignSegmenter:
    """
    Consumes one feature vector per frame (from LandmarkExtractor) and
    yields closed SignWindow objects when it believes a complete sign has
    been performed.

    Usage:
        seg = SignSegmenter()
        for frame_vec, presence in stream:
            window = seg.push(frame_vec, hands_present=presence)
            if window is not None:
                # hand this window to the recognition model
                ...
    """

    def __init__(self, config: Optional[SegmentationConfig] = None, centroid_fn=None):
        """
        centroid_fn: optional callable(feature_vec) -> np.ndarray(2,), used
        to compute a 2D centroid for velocity tracking. Defaults to
        _hand_centroid, which assumes the hand-based feature layout from
        LandmarkExtractor.to_feature_vector() (188-dim, hand slots at
        [0:63]/[63:126]). Pass a different extractor for other feature
        layouts (e.g. the pose-only 60-dim vectors used by the real-time
        WebSocket path — see app/websocket/recognize_ws.py) rather than
        silently feeding it a layout it wasn't built for.
        """
        self.cfg = config or SegmentationConfig()
        self._centroid_fn = centroid_fn or self._hand_centroid
        self._prev_centroid: Optional[np.ndarray] = None
        self._velocity_history: Deque[float] = collections.deque(
            maxlen=self.cfg.velocity_smoothing
        )
        self._state = HandState.IDLE
        self._idle_run = 0
        self._current_window: Optional[SignWindow] = None
        self._active_frame_count = 0  # frames with real motion/hold, excludes buffered idle tail
        self._frame_idx = 0

    @staticmethod
    def _hand_centroid(feature_vec: np.ndarray) -> np.ndarray:
        """
        Centroid of whichever hand(s) are present, computed from the
        feature vector layout produced by LandmarkExtractor.to_feature_vector.
        Uses only the x,y of each landmark for velocity (z is noisier).
        """
        left = feature_vec[0:63].reshape(21, 3)
        right = feature_vec[63:126].reshape(21, 3)
        left_present, right_present = feature_vec[-2], feature_vec[-1]

        points = []
        if left_present > 0.5:
            points.append(left[:, :2])
        if right_present > 0.5:
            points.append(right[:, :2])
        if not points:
            return np.zeros(2, dtype=np.float32)
        return np.concatenate(points, axis=0).mean(axis=0)

    def push(self, feature_vec: np.ndarray, hands_present: bool) -> Optional[SignWindow]:
        """
        Feed one frame's feature vector in. Returns a completed SignWindow
        if this frame closed one, else None.
        """
        self._frame_idx += 1
        centroid = self._centroid_fn(feature_vec)

        raw_velocity = (
            float(np.linalg.norm(centroid - self._prev_centroid))
            if self._prev_centroid is not None
            else 0.0
        )
        self._prev_centroid = centroid
        self._velocity_history.append(raw_velocity)
        smoothed_velocity = float(np.mean(self._velocity_history))

        if not hands_present:
            new_state = HandState.IDLE
        elif smoothed_velocity > self.cfg.velocity_threshold:
            new_state = HandState.MOVING
        else:
            new_state = HandState.HOLDING

        closed_window: Optional[SignWindow] = None

        if new_state in (HandState.MOVING, HandState.HOLDING):
            self._idle_run = 0
            if self._current_window is None:
                self._current_window = SignWindow(
                    start_frame=self._frame_idx, end_frame=self._frame_idx, feature_vectors=[]
                )
            self._current_window.feature_vectors.append(feature_vec)
            self._current_window.end_frame = self._frame_idx
            self._active_frame_count += 1

            if self._current_window.length >= self.cfg.max_window_frames:
                closed_window = self._close_window()

        else:  # IDLE
            self._idle_run += 1
            if self._current_window is not None:
                # keep buffering briefly through the idle frames so we don't
                # clip the tail end of the sign's return-to-rest motion
                self._current_window.feature_vectors.append(feature_vec)
                if self._idle_run >= self.cfg.idle_frames_to_close_window:
                    closed_window = self._close_window()

        self._state = new_state
        return closed_window

    def _close_window(self) -> Optional[SignWindow]:
        window = self._current_window
        active_frames = self._active_frame_count
        self._current_window = None
        self._active_frame_count = 0
        self._idle_run = 0
        # Use active (moving/holding) frame count, not total buffered length,
        # so a couple of idle "tail" frames buffered while closing the window
        # can't push a brief noise blip over the minimum-length bar.
        if window is None or active_frames < self.cfg.min_window_frames:
            return None  # too short — treat as noise, not a sign
        return window

    def flush(self) -> Optional[SignWindow]:
        """
        Force-close whatever window is currently open, without waiting for
        the usual idle-frames-to-close condition. For a genuinely
        continuous live stream this should rarely be needed (idle gaps
        between signs close windows naturally) — it exists for the case
        where the stream itself ends mid-sign: a single clip streamed
        start-to-finish with no trailing idle frames (this is exactly what
        happens when testing against this project's one-sign-per-clip
        dataset), or a user stopping the camera right as they finish
        signing. Still enforces min_window_frames so it can't be used to
        smuggle a noise blip through as a false close.
        """
        return self._close_window()


class PredictionDebouncer:
    """
    Stability layer for §8: suppresses re-emitting the same recognized
    label on consecutive windows unless the signer's hands returned to
    idle in between (i.e. they deliberately re-signed it) or a
    configurable number of frames have passed.

    This is intentionally decoupled from SignSegmenter so it can also be
    used to debounce raw per-frame classifier output if you later add a
    lower-latency, non-windowed path.
    """

    def __init__(self, suppress_repeats: bool = True):
        self.suppress_repeats = suppress_repeats
        self._last_label: Optional[str] = None

    def should_emit(self, label: str, went_idle_since_last: bool) -> bool:
        if not self.suppress_repeats:
            return True
        if label != self._last_label or went_idle_since_last:
            self._last_label = label
            return True
        return False

    def reset(self):
        self._last_label = None
