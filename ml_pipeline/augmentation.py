"""
Data Augmentation
------------------
Applied only to the training split, never to validation/test — augmenting
val/test would let the model get evaluated on easier, less varied data than
what it'll actually see in production, hiding real performance problems.

These are standard Keras preprocessing layers rather than a custom
implementation because they run on-GPU/TPU as part of the model graph
during training (fast), and Keras handles train-vs-inference behavior
automatically (e.g. RandomFlip does nothing at inference time).
"""
from __future__ import annotations

import tensorflow as tf
from tensorflow.keras import layers


def build_augmentation_pipeline() -> tf.keras.Sequential:
    return tf.keras.Sequential(
        [
            layers.RandomFlip("horizontal"),
            layers.RandomRotation(0.05),        # +/- ~18 degrees
            layers.RandomZoom(0.1),
            layers.RandomContrast(0.15),
            layers.RandomBrightness(0.15),
        ],
        name="augmentation",
    )
