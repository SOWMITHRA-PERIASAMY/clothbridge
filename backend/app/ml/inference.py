"""
Model Inference Wrapper
-------------------------
Loads a REAL trained TFLite model from disk. Does not fabricate predictions.
If no trained model file is found, predict() raises ModelNotTrainedError
loudly instead of returning fake confidence scores.

Once you've trained the model on Colab, drop model.tflite and labels.txt
into backend/app/ml/artifacts/ and this class picks it up automatically.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from app.schemas.donation import DefectDetection, DefectType

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
MODEL_PATH = ARTIFACTS_DIR / "model.tflite"
LABELS_PATH = ARTIFACTS_DIR / "labels.txt"

IMAGE_SIZE = (224, 224)


class ModelNotTrainedError(RuntimeError):
    """Raised when inference is requested but no trained model artifact exists yet."""


class ClothingQualityModel:
    def __init__(self) -> None:
        self._interpreter = None
        self._labels: list[str] = []
        self._loaded = False

    @property
    def is_trained(self) -> bool:
        return MODEL_PATH.exists() and LABELS_PATH.exists()

    def _lazy_load(self) -> None:
        if self._loaded:
            return
        if not MODEL_PATH.exists() or not LABELS_PATH.exists():
            raise ModelNotTrainedError(
                f"No trained model found at {MODEL_PATH}. Run "
                "ml_pipeline/train.py (see ml_pipeline/README.md for the "
                "Colab instructions) and place model.tflite + labels.txt in "
                f"{ARTIFACTS_DIR} before calling predict()."
            )
        try:
            import tflite_runtime.interpreter as tflite
        except ImportError:
            import tensorflow as tf
            tflite = tf.lite

        self._interpreter = tflite.Interpreter(model_path=str(MODEL_PATH))
        self._interpreter.allocate_tensors()
        self._labels = LABELS_PATH.read_text().strip().splitlines()
        self._loaded = True

    def predict(self, image_array: np.ndarray) -> list[DefectDetection]:
        self._lazy_load()
        assert self._interpreter is not None

        input_details = self._interpreter.get_input_details()
        output_details = self._interpreter.get_output_details()

        batched = np.expand_dims(image_array.astype(np.float32), axis=0)
        self._interpreter.set_tensor(input_details[0]["index"], batched)
        self._interpreter.invoke()
        raw_output = self._interpreter.get_tensor(output_details[0]["index"])[0]

        detections: list[DefectDetection] = []
        for label, confidence in zip(self._labels, raw_output):
            try:
                defect = DefectType(label.lower())
            except ValueError:
                continue
            detections.append(
                DefectDetection(
                    defect=defect,
                    confidence=float(confidence),
                    severity=float(confidence),
                )
            )
        return detections

    def model_version(self) -> str:
        meta_path = ARTIFACTS_DIR / "metadata.json"
        if meta_path.exists():
            return json.loads(meta_path.read_text()).get("version", "unknown")
        return "untrained"
