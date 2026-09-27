"""
Tests SignSegmenter against a scripted motion sequence: idle -> a hand
sweeps into frame and moves -> holds still -> returns to idle.
This is synthetic *motion data* used to test the segmentation algorithm's
logic (thresholds, window open/close) — it is explicitly NOT training data
for the recognition model and makes no claim about recognizing any real
ISL sign. See ml/training/README.md for the real-dataset requirement.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ml", "preprocessing"))

import numpy as np
from landmark_extractor import FRAME_FEATURE_DIM
from sign_segmenter import SignSegmenter, SegmentationConfig


def make_frame(hand_center_xy, hand_present=True):
    """Builds a synthetic feature vector with a hand of fixed shape at a given centroid."""
    vec = np.zeros(FRAME_FEATURE_DIM, dtype=np.float32)
    if hand_present:
        base_hand = np.tile(np.array(hand_center_xy + (0.0,), dtype=np.float32), (21, 1))
        base_hand += np.random.normal(0, 0.01, size=(21, 3)).astype(np.float32)  # finger spread jitter
        vec[0:63] = base_hand.flatten()  # left hand slot
        vec[-2] = 1.0  # left_hand_present flag
    return vec


def test_idle_then_sign_then_idle_produces_one_window():
    seg = SignSegmenter(SegmentationConfig(
        velocity_threshold=0.05,
        idle_frames_to_close_window=5,
        min_window_frames=3,
    ))

    windows = []

    # 15 idle frames (no hand)
    for _ in range(15):
        w = seg.push(make_frame((0, 0), hand_present=False), hands_present=False)
        if w: windows.append(w)

    # hand sweeps in and moves for 10 frames
    for i in range(10):
        w = seg.push(make_frame((0.3 + i * 0.05, 0.3), hand_present=True), hands_present=True)
        if w: windows.append(w)

    # hand holds still for 10 frames (static portion of the sign)
    for _ in range(10):
        w = seg.push(make_frame((0.8, 0.3), hand_present=True), hands_present=True)
        if w: windows.append(w)

    # returns to idle for long enough to close the window
    for _ in range(10):
        w = seg.push(make_frame((0, 0), hand_present=False), hands_present=False)
        if w: windows.append(w)

    assert len(windows) == 1, f"expected exactly 1 sign window, got {len(windows)}"
    win = windows[0]
    assert win.length >= 3
    print(f"PASS: single continuous sign -> exactly 1 window, {win.length} frames "
          f"(frames {win.start_frame}-{win.end_frame})")


def test_two_separate_signs_produce_two_windows():
    seg = SignSegmenter(SegmentationConfig(
        velocity_threshold=0.05,
        idle_frames_to_close_window=5,
        min_window_frames=3,
    ))
    windows = []

    def run(frames):
        for f, present in frames:
            w = seg.push(f, present)
            if w: windows.append(w)

    # sign 1
    run([(make_frame((0, 0), False), False)] * 6)
    run([(make_frame((0.2 + i*0.05, 0.2), True), True) for i in range(8)])
    run([(make_frame((0, 0), False), False)] * 8)  # gap between signs

    # sign 2
    run([(make_frame((0.5 + i*0.05, 0.5), True), True) for i in range(8)])
    run([(make_frame((0, 0), False), False)] * 8)

    assert len(windows) == 2, f"expected 2 separate sign windows, got {len(windows)}"
    print(f"PASS: two signs with a rest gap between them -> {len(windows)} separate windows")


def test_brief_jitter_does_not_open_a_window():
    """A single stray frame of 'motion' (sensor noise) below min_window_frames should be discarded."""
    seg = SignSegmenter(SegmentationConfig(
        velocity_threshold=0.05,
        idle_frames_to_close_window=3,
        min_window_frames=5,
    ))
    windows = []
    for _ in range(5):
        w = seg.push(make_frame((0, 0), False), False)
        if w: windows.append(w)
    # 2 frames of jitter only — shorter than min_window_frames
    for i in range(2):
        w = seg.push(make_frame((0.4 + i*0.1, 0.4), True), True)
        if w: windows.append(w)
    for _ in range(5):
        w = seg.push(make_frame((0, 0), False), False)
        if w: windows.append(w)

    assert len(windows) == 0, f"expected jitter to be discarded as noise, got {len(windows)} windows"
    print("PASS: brief 2-frame jitter below min_window_frames is correctly discarded as noise")


if __name__ == "__main__":
    test_idle_then_sign_then_idle_produces_one_window()
    test_two_separate_signs_produce_two_windows()
    test_brief_jitter_does_not_open_a_window()
    print("\nAll sign segmenter tests passed.")
