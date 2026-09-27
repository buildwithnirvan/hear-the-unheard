"""
isl_classifier.py

Loads the trained pose classifier (ml/models/pose_classifier_v1.joblib)
once at import time and exposes a real predict() function. Returns None
cleanly if no model has been trained/registered yet — callers must not
fabricate a result in that case (see app/api/v1/recognize.py).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import joblib
import numpy as np

ML_ROOT = Path(__file__).parent.parent.parent.parent.parent / "ml"
sys.path.insert(0, str(ML_ROOT / "preprocessing"))
sys.path.insert(0, str(ML_ROOT / "training"))

MODEL_PATH = ML_ROOT / "models" / "pose_classifier_v1.joblib"
CLASSES_PATH = ML_ROOT / "models" / "pose_classifier_v1_classes.json"


class ISLClassifier:
    def __init__(self):
        self.model = None
        self.classes: list[str] = []
        self._load()

    def _load(self):
        if MODEL_PATH.exists() and CLASSES_PATH.exists():
            self.model = joblib.load(MODEL_PATH)
            self.classes = json.loads(CLASSES_PATH.read_text())

    @property
    def is_available(self) -> bool:
        return self.model is not None

    def predict_from_sequence(self, pose_sequence: np.ndarray, top_k: int = 3) -> Optional[list[dict]]:
        """
        pose_sequence: (num_frames, feature_dim) normalized pose landmarks,
        same format extract_dataset_landmarks.py produces.
        Returns None if no model is loaded (honest — caller must not fake
        a result), else a list of {gloss, confidence} sorted descending.
        """
        if not self.is_available:
            return None

        from train_pose_classifier import sequence_to_features  # local import: only needed here

        features = sequence_to_features(pose_sequence).reshape(1, -1)
        probs = self.model.predict_proba(features)[0]
        top_indices = np.argsort(probs)[::-1][:top_k]
        return [
            {"gloss": self.classes[i].upper(), "confidence": float(probs[i])}
            for i in top_indices
        ]


# Singleton — loaded once per process, matching how a real deployment would work.
_classifier: Optional[ISLClassifier] = None


def get_classifier() -> ISLClassifier:
    global _classifier
    if _classifier is None:
        _classifier = ISLClassifier()
    return _classifier
