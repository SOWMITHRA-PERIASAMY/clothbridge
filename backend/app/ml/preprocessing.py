"""
Shared image preprocessing — MUST stay identical to ml_pipeline/dataset_preprocessing.py
so that inference-time preprocessing matches training-time preprocessing exactly.
A mismatch here (e.g. different resize/normalization) is one of the most common
causes of "model works in training but garbage in production" bugs — keep this
file and the training-side one in sync.
"""
from __future__ import annotations

import io

import numpy as np
import requests
from PIL import Image

IMAGE_SIZE = (224, 224)


def load_and_preprocess_image(image_url: str) -> np.ndarray:
    """Fetch an image (from a Firebase Storage URL) and preprocess it into
    the exact tensor shape/scale the model expects."""
    response = requests.get(image_url, timeout=10)
    response.raise_for_status()
    image = Image.open(io.BytesIO(response.content)).convert("RGB")
    return preprocess_pil_image(image)


def preprocess_pil_image(image: Image.Image) -> np.ndarray:
    image = image.resize(IMAGE_SIZE)
    array = np.asarray(image, dtype=np.float32) / 255.0  # EfficientNet-style [0,1] scaling
    return array
