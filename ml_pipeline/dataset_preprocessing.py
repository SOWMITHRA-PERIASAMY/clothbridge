"""
Dataset Preprocessing
----------------------
Reads the output of synthetic_data_generator.py (images/ + labels/ + manifest.csv)
and builds a tf.data.Dataset ready for training.

LABEL ENCODING — read this before changing DEFECT_LABELS:
The model predicts a multi-label vector, one sigmoid output per defect type
in DEFECT_LABELS. This order MUST match labels.txt written at the end of
train.py, and MUST match app/ml/inference.py's expectation on the backend
(it zips labels.txt lines against DefectType enum values in order). Change
it in exactly one place if you ever add a defect type — here — and rerun
both synthetic_data_generator.py and train.py.

A "none"/Grade-A sample has an all-zero label vector: the model just needs
to output low confidence across every defect, which is what "clean" means.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import tensorflow as tf

IMAGE_SIZE = (224, 224)  # EfficientNetB0 default input resolution

# Order matters — see docstring above.
DEFECT_LABELS = ["tear", "hole", "stain", "dirt", "fade", "heavy_wear"]

GRADE_TO_DECISION = {
    "A": "accept",
    "B": "repair_upcycle",
    "C": "repair_upcycle",
    "D": "reject_recycle",
}


def load_manifest(synthetic_output_dir: Path) -> pd.DataFrame:
    manifest_path = synthetic_output_dir / "manifest.csv"
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"No manifest.csv found at {manifest_path}. Run "
            "synthetic_data_generator.py first (see its module docstring)."
        )
    df = pd.read_csv(manifest_path)
    df["image_path"] = df["sample_id"].apply(
        lambda sid: str(synthetic_output_dir / "images" / f"{sid}.jpg")
    )
    df["label_path"] = df["sample_id"].apply(
        lambda sid: str(synthetic_output_dir / "labels" / f"{sid}.json")
    )
    df["decision"] = df["grade"].map(GRADE_TO_DECISION)
    return df


def build_label_vector(defect: str) -> np.ndarray:
    """One sample = one active defect (or none). Returns a multi-hot vector
    even though only one entry is ever 1.0 today — this keeps the model
    architecture correct for real photos later, which may show *combined*
    defects (e.g. a stain AND a tear on the same garment)."""
    vec = np.zeros(len(DEFECT_LABELS), dtype=np.float32)
    if defect in DEFECT_LABELS:
        idx = DEFECT_LABELS.index(defect)
        vec[idx] = 1.0
    return vec


def _decode_image(path: tf.Tensor) -> tf.Tensor:
    raw = tf.io.read_file(path)
    image = tf.io.decode_jpeg(raw, channels=3)
    image = tf.image.resize(image, IMAGE_SIZE)
    image = tf.cast(image, tf.float32) / 255.0
    return image


def dataframe_to_dataset(
    df: pd.DataFrame,
    batch_size: int = 32,
    shuffle: bool = True,
    seed: int = 42,
) -> tf.data.Dataset:
    labels = np.stack([build_label_vector(d) for d in df["defect"]])
    paths = df["image_path"].values

    ds = tf.data.Dataset.from_tensor_slices((paths, labels))
    if shuffle:
        ds = ds.shuffle(buffer_size=len(df), seed=seed, reshuffle_each_iteration=True)

    def _load(path, label):
        return _decode_image(path), label

    ds = ds.map(_load, num_parallel_calls=tf.data.AUTOTUNE)
    ds = ds.batch(batch_size)
    ds = ds.prefetch(tf.data.AUTOTUNE)
    return ds


def stratified_split(
    df: pd.DataFrame,
    val_frac: float = 0.1,
    test_frac: float = 0.1,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Splits per-grade so rare classes aren't accidentally left out of
    validation/test entirely — plain random splitting can do that when a
    class is a small fraction of the dataset."""
    train_parts, val_parts, test_parts = [], [], []
    rng = np.random.RandomState(seed)

    for grade, group in df.groupby("grade"):
        group = group.sample(frac=1.0, random_state=rng.randint(0, 1_000_000)).reset_index(drop=True)
        n = len(group)
        n_val = max(1, int(n * val_frac))
        n_test = max(1, int(n * test_frac))
        val_parts.append(group.iloc[:n_val])
        test_parts.append(group.iloc[n_val:n_val + n_test])
        train_parts.append(group.iloc[n_val + n_test:])

    train_df = pd.concat(train_parts).sample(frac=1.0, random_state=seed).reset_index(drop=True)
    val_df = pd.concat(val_parts).sample(frac=1.0, random_state=seed).reset_index(drop=True)
    test_df = pd.concat(test_parts).sample(frac=1.0, random_state=seed).reset_index(drop=True)
    return train_df, val_df, test_df
