"""
predict.py — Quick sanity check: run the trained model on one image from
the command line, without going through the FastAPI backend.

Usage:
    python predict.py path/to/some_shirt.jpg
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import tensorflow as tf
from PIL import Image

from dataset_preprocessing import DEFECT_LABELS, IMAGE_SIZE

BASE_DIR = Path(__file__).parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"


def load_and_preprocess(image_path: str) -> np.ndarray:
    image = Image.open(image_path).convert("RGB").resize(IMAGE_SIZE)
    array = np.asarray(image, dtype=np.float32) / 255.0
    return np.expand_dims(array, axis=0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("image_path")
    parser.add_argument(
        "--model", default=str(ARTIFACTS_DIR / "model.keras"),
        help="Path to a .keras model (defaults to the freshly trained one)",
    )
    args = parser.parse_args()

    model_path = Path(args.model)
    if not model_path.exists():
        raise SystemExit(
            f"No trained model found at {model_path}. Run train.py first "
            "(on Colab with a GPU, using real assets — not placeholders)."
        )

    model = tf.keras.models.load_model(model_path)
    batch = load_and_preprocess(args.image_path)
    predictions = model.predict(batch)[0]

    result = {
        label: round(float(confidence), 4)
        for label, confidence in zip(DEFECT_LABELS, predictions)
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
