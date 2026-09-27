"""
train_pose_classifier.py

Trains a real ISL word-sign classifier on the pose-landmark sequences
extracted by extract_dataset_landmarks.py.

MODEL CHOICE — why not an LSTM/Transformer here: with 76 classes and as
few as 3-8 samples per class (see class distribution printed at runtime),
a deep temporal model would overfit badly and any accuracy number from it
would be meaningless. A classical model trained on hand-engineered
per-sequence statistics (mean/std/min/max/first/last per landmark
dimension) is the honest choice for this data size — it's what actually
generalizes with this little data per class, not what looks most
sophisticated.

SCOPE — read this before trusting any number this script prints: this
model only sees pose (shoulder/elbow/wrist) landmarks, not hand shape
(see extract_dataset_landmarks.py docstring for why). It can only
distinguish signs that differ in gross arm/body movement and position.
Many ISL sign pairs are near-identical in arm trajectory and differ only
in hand configuration — this model cannot and will not tell those apart,
and its per-class accuracy will show that honestly.

Evaluation: stratified K-fold cross-validation (K chosen per the
smallest class's sample count, since some classes have as few as 3
samples). Reported accuracy/F1 are the cross-validated ones, not train
accuracy, which is not fed to the ModelVersion DB row.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict

LANDMARKS_ROOT = Path(__file__).parent.parent / "datasets" / "landmarks"
MODEL_OUT = Path(__file__).parent.parent / "models"


def sequence_to_features(seq: np.ndarray) -> np.ndarray:
    """
    seq: (num_frames, feature_dim) normalized pose landmarks for one clip.
    Returns a fixed-length descriptor: mean, std, min, max, and
    (last-first) delta across time, per landmark dimension.
    """
    mean = seq.mean(axis=0)
    std = seq.std(axis=0)
    mn = seq.min(axis=0)
    mx = seq.max(axis=0)
    delta = seq[-1] - seq[0]
    return np.concatenate([mean, std, mn, mx, delta]).astype(np.float32)


def load_dataset():
    classes = sorted(d.name for d in LANDMARKS_ROOT.iterdir() if d.is_dir())
    X, y, sample_paths = [], [], []
    for class_idx, class_name in enumerate(classes):
        for npy_file in sorted((LANDMARKS_ROOT / class_name).glob("*.npy")):
            seq = np.load(npy_file)
            X.append(sequence_to_features(seq))
            y.append(class_idx)
            sample_paths.append(str(npy_file))
    return np.stack(X), np.array(y), classes, sample_paths


def run():
    print("Loading dataset...")
    X, y, classes, sample_paths = load_dataset()
    print(f"Loaded {len(X)} samples across {len(classes)} classes, feature dim={X.shape[1]}")

    class_counts = np.bincount(y)
    min_class_count = int(class_counts.min())
    n_splits = max(2, min(5, min_class_count))
    print(f"Smallest class has {min_class_count} samples -> using {n_splits}-fold stratified CV")

    clf = RandomForestClassifier(
        n_estimators=300,
        max_depth=None,
        min_samples_leaf=1,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )

    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    y_pred = cross_val_predict(clf, X, y, cv=skf)

    accuracy = float((y_pred == y).mean())
    f1_macro = float(f1_score(y, y_pred, average="macro"))
    cm = confusion_matrix(y, y_pred).tolist()

    print(f"\nCross-validated accuracy: {accuracy:.3f}")
    print(f"Cross-validated macro F1: {f1_macro:.3f}")

    # Per-class accuracy — the honest, useful number, since macro accuracy
    # hides which specific signs this model actually can/can't tell apart.
    per_class_acc = {}
    for class_idx, class_name in enumerate(classes):
        mask = y == class_idx
        if mask.sum() == 0:
            continue
        per_class_acc[class_name] = float((y_pred[mask] == y[mask]).mean())

    worst = sorted(per_class_acc.items(), key=lambda kv: kv[1])[:10]
    best = sorted(per_class_acc.items(), key=lambda kv: -kv[1])[:10]
    print("\nWorst-recognized classes (cross-validated):")
    for name, acc in worst:
        print(f"  {name}: {acc:.2f}")
    print("\nBest-recognized classes (cross-validated):")
    for name, acc in best:
        print(f"  {name}: {acc:.2f}")

    # Fit final model on ALL data for deployment. Its accuracy on data it
    # was trained on is not a meaningful metric and is deliberately not
    # computed/reported here — only the CV numbers above go in the model
    # card and the database.
    clf.fit(X, y)

    MODEL_OUT.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, MODEL_OUT / "pose_classifier_v1.joblib")
    with open(MODEL_OUT / "pose_classifier_v1_classes.json", "w") as f:
        json.dump(classes, f, indent=2)

    model_card = {
        "version_tag": "ISL Pose Classifier v1.0",
        "model_type": "RandomForestClassifier (scikit-learn)",
        "feature_type": "pose-only (shoulder/elbow/wrist), NOT hand shape — see module docstring",
        "num_classes": len(classes),
        "classes": classes,
        "num_samples": len(X),
        "min_samples_per_class": min_class_count,
        "cv_folds": n_splits,
        "cross_validated_accuracy": accuracy,
        "cross_validated_macro_f1": f1_macro,
        "per_class_cv_accuracy": per_class_acc,
        "confusion_matrix": cm,
        "limitations": [
            "Trained on pose (arm/body) landmarks only, not hand shape — "
            "cannot reliably distinguish signs that differ mainly in hand "
            "configuration rather than arm movement/position.",
            f"{min_class_count}-{int(class_counts.max())} samples per class "
            "is a small-data regime; per-class accuracy varies a lot — see "
            "per_class_cv_accuracy, do not trust the macro average alone "
            "for any specific sign.",
            "Source videos are a specific dataset (see ml/training/README.md) "
            "recorded in a fairly uniform setting; real-world webcam "
            "conditions (lighting, camera angle, signer variation) are "
            "untested.",
        ],
    }
    with open(MODEL_OUT / "pose_classifier_v1_model_card.json", "w") as f:
        json.dump(model_card, f, indent=2)

    print(f"\nSaved model to {MODEL_OUT / 'pose_classifier_v1.joblib'}")
    print(f"Saved model card to {MODEL_OUT / 'pose_classifier_v1_model_card.json'}")
    return model_card


if __name__ == "__main__":
    run()
