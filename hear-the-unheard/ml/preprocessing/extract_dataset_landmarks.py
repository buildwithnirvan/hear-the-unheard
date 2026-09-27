"""
extract_dataset_landmarks.py

Batch-processes every clip in the uploaded ISL dataset into pose landmark
sequences and saves them to ml/datasets/landmarks/.

WHY POSE-ONLY: the uploaded dataset's videos have a MediaPipe hand-landmark
visualization burned into the pixels (colored fingertip dots + bounding
box) — see docs/STATUS.md for how this was discovered. Our hand detector
gets 0% detections on it because the overlay distorts the hand's actual
appearance. Pose detection is unaffected (confirmed 100% detection in
testing) because MediaPipe Pose reasons about overall body silhouette,
not fine hand-region pixels.

This is also the RIGHT choice for reliability, not just a fallback:
training on the hand-region pixels of this data (or on hand landmarks
somehow reverse-engineered from the overlay) would mean the model learns
to key off overlay artifacts that will NOT exist in real webcam input at
inference time — a train/inference mismatch that would make the model
useless in production. Pose landmarks have no such dependency on the
overlay, so a pose-based model trained here generalizes honestly to real
signing video.

LIMITATION this implies: a pose-only model can only learn to distinguish
signs by gross arm/body movement and position, not by hand shape/finger
configuration, which is what actually differentiates a lot of ISL
vocabulary. This is documented, not hidden — see model card written by
train_pose_classifier.py after training.

Output layout:
  ml/datasets/landmarks/<class_name>/<video_stem>.npy
    shape: (num_frames, POSE_FEATURE_DIM) float32, normalized per-frame
           via the same shoulder-centered/shoulder-width normalization
           LandmarkExtractor uses, so it stays consistent with the rest
           of the pipeline.
  ml/datasets/landmarks/extraction_manifest.json
    per-class counts, failures, total runtime — real numbers, not
    estimates.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from landmark_extractor import UPPER_BODY_POSE_INDICES, LandmarkExtractor  # noqa: E402

RAW_ROOT = Path(__file__).parent.parent / "datasets" / "raw" / "kaggle_isl_landmarks" / "ProcessedData_vivit"
OUT_ROOT = Path(__file__).parent.parent / "datasets" / "landmarks"

POSE_FEATURE_DIM = len(UPPER_BODY_POSE_INDICES) * 4  # x,y,z,visibility per point


def extract_pose_sequence(video_path: Path, pose_model) -> np.ndarray | None:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return None

    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = pose_model.process(rgb)
        if result.pose_landmarks is None:
            frames.append(np.zeros(POSE_FEATURE_DIM, dtype=np.float32))
            continue
        pose = np.array(
            [[lm.x, lm.y, lm.z, lm.visibility] for lm in result.pose_landmarks.landmark],
            dtype=np.float32,
        )
        normalized = LandmarkExtractor._normalize_pose_subset(pose)
        frames.append(normalized.flatten())

    cap.release()
    if not frames:
        return None
    return np.stack(frames, axis=0)


def run(limit_per_class: int | None = None):
    if not RAW_ROOT.exists():
        print(f"ERROR: {RAW_ROOT} not found.")
        sys.exit(1)

    classes = sorted(d.name for d in RAW_ROOT.iterdir() if d.is_dir())
    print(f"Found {len(classes)} classes under {RAW_ROOT}")

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    pose_model = mp.solutions.pose.Pose(
        static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5
    )

    manifest = {"classes": {}, "failures": [], "started_at": time.time()}
    t_start = time.time()
    total_done = 0
    total_files = sum(
        len(list((RAW_ROOT / c).glob("*.MOV"))[:limit_per_class]) for c in classes
    )

    for class_name in classes:
        class_dir = RAW_ROOT / class_name
        out_dir = OUT_ROOT / class_name
        out_dir.mkdir(parents=True, exist_ok=True)

        video_files = sorted(class_dir.glob("*.MOV"))
        if limit_per_class:
            video_files = video_files[:limit_per_class]

        ok_count = 0
        for vf in video_files:
            out_path = out_dir / f"{vf.stem}.npy"
            if out_path.exists():
                ok_count += 1
                total_done += 1
                continue  # resumable: skip work already done in a previous run

            seq = extract_pose_sequence(vf, pose_model)
            if seq is None:
                manifest["failures"].append(str(vf.relative_to(RAW_ROOT)))
                continue
            np.save(out_path, seq)
            ok_count += 1
            total_done += 1

            if total_done % 50 == 0:
                elapsed = time.time() - t_start
                rate = total_done / elapsed
                eta = (total_files - total_done) / rate if rate > 0 else float("nan")
                print(f"[{total_done}/{total_files}] elapsed={elapsed:.0f}s eta={eta:.0f}s", flush=True)

        manifest["classes"][class_name] = {"total": len(video_files), "succeeded": ok_count}
        print(f"  {class_name}: {ok_count}/{len(video_files)} extracted", flush=True)

    pose_model.close()
    manifest["finished_at"] = time.time()
    manifest["total_runtime_seconds"] = manifest["finished_at"] - manifest["started_at"]
    manifest["total_videos"] = total_files
    manifest["total_succeeded"] = total_done
    manifest["total_failed"] = len(manifest["failures"])

    with open(OUT_ROOT / "extraction_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nDone. {total_done}/{total_files} extracted in {manifest['total_runtime_seconds']:.0f}s")
    print(f"Manifest written to {OUT_ROOT / 'extraction_manifest.json'}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--limit-per-class", type=int, default=None)
    args = parser.parse_args()
    run(limit_per_class=args.limit_per_class)
