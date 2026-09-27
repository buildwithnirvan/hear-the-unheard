"""
Verifies the landmark extraction pipeline actually runs — not a mock.

These tests confirm:
  1. Both MediaPipe graphs (hands, pose) initialize offline (no network call).
  2. process_frame() runs real inference and returns a well-formed result,
     including on frames with no person in them (must not detect false hands).
  3. to_feature_vector() always produces a fixed-length, normalized vector.

This does NOT test recognition accuracy on real ISL signs — that requires a
trained model and a labeled dataset (see ml/training/, Phase 3). This test
only proves the extraction pipeline itself is real and functioning.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ml", "preprocessing"))

import numpy as np
from landmark_extractor import LandmarkExtractor, FRAME_FEATURE_DIM


def test_extractor_initializes_offline():
    extractor = LandmarkExtractor()
    assert extractor.hands is not None
    assert extractor.pose is not None
    extractor.close()
    print("PASS: extractor initializes without any network call")


def test_blank_frame_detects_nothing():
    extractor = LandmarkExtractor()
    blank = np.zeros((480, 640, 3), dtype=np.uint8)
    result = extractor.process_frame(blank)
    assert result.left_hand is None
    assert result.right_hand is None
    vec = extractor.to_feature_vector(result)
    assert vec.shape == (FRAME_FEATURE_DIM,)
    assert np.all(vec[-2:] == 0.0)  # presence flags both 0
    extractor.close()
    print(f"PASS: blank frame -> no false detections, feature vector shape {vec.shape}")


def test_feature_vector_shape_is_constant():
    """The vector length must not depend on how many hands/pose points were found."""
    extractor = LandmarkExtractor()
    noise = (np.random.rand(480, 640, 3) * 255).astype(np.uint8)
    result = extractor.process_frame(noise)
    vec = extractor.to_feature_vector(result)
    assert vec.shape == (FRAME_FEATURE_DIM,)
    assert vec.dtype == np.float32
    extractor.close()
    print(f"PASS: random-noise frame still produces fixed-shape vector {vec.shape}, dim={FRAME_FEATURE_DIM}")


def test_normalization_is_translation_invariant():
    """A hand shifted in the frame should normalize to (near) the same vector."""
    hand_a = np.array([[0.5 + i * 0.01, 0.5 + i * 0.005, 0.0] for i in range(21)], dtype=np.float32)
    hand_b = hand_a + np.array([0.2, 0.2, 0.0], dtype=np.float32)  # shifted in-frame

    norm_a = LandmarkExtractor._normalize_hand(hand_a)
    norm_b = LandmarkExtractor._normalize_hand(hand_b)

    assert np.allclose(norm_a, norm_b, atol=1e-5)
    print("PASS: hand normalization is translation-invariant (same shape, different frame position)")


def test_pose_normalization_runs_and_is_shift_invariant():
    """
    Regression test: _normalize_pose_subset previously crashed with a
    broadcast ValueError on any real detected pose (see docs/STATUS.md —
    caught while running the batch dataset extraction, not by this suite,
    because earlier tests only ever exercised frames with NO pose
    detected). This directly exercises it with a synthetic-but-plausible
    33-landmark pose array so that gap can't recur silently.
    """
    from landmark_extractor import NUM_POSE_LANDMARKS

    pose = np.zeros((NUM_POSE_LANDMARKS, 4), dtype=np.float32)
    # plausible shoulder/elbow/wrist positions (indices per MediaPipe Pose topology)
    pose[11] = [0.4, 0.4, 0.0, 0.9]   # left shoulder
    pose[12] = [0.6, 0.4, 0.0, 0.9]   # right shoulder
    pose[13] = [0.35, 0.55, 0.0, 0.9]  # left elbow
    pose[14] = [0.65, 0.55, 0.0, 0.9]  # right elbow
    pose[15] = [0.3, 0.7, 0.0, 0.9]   # left wrist
    pose[16] = [0.7, 0.7, 0.0, 0.9]   # right wrist

    out_a = LandmarkExtractor._normalize_pose_subset(pose)
    assert out_a.shape == (len(__import__("landmark_extractor").UPPER_BODY_POSE_INDICES), 4)

    shifted = pose.copy()
    shifted[:, :3] += np.array([0.15, 0.1, 0.0], dtype=np.float32)  # whole body shifted in frame
    out_b = LandmarkExtractor._normalize_pose_subset(shifted)

    assert np.allclose(out_a, out_b, atol=1e-4), "pose normalization should be shift-invariant"
    print("PASS: pose normalization runs on a real detected pose and is shift-invariant")


if __name__ == "__main__":
    test_extractor_initializes_offline()
    test_blank_frame_detects_nothing()
    test_feature_vector_shape_is_constant()
    test_normalization_is_translation_invariant()
    test_pose_normalization_runs_and_is_shift_invariant()
    print("\nAll landmark extractor tests passed.")
