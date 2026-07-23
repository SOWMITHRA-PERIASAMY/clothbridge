"""
evaluate.py — Held-out test set evaluation.

Called automatically at the end of train.py, but can also be run standalone
against a saved model.keras to re-generate reports without retraining:
    python evaluate.py --model artifacts/model.keras
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix

from dataset_preprocessing import DEFECT_LABELS, dataframe_to_dataset, load_manifest, stratified_split

BASE_DIR = Path(__file__).parent


def evaluate_model(
    model: tf.keras.Model,
    test_ds: tf.data.Dataset,
    test_df: pd.DataFrame,
    reports_dir: Path,
    threshold: float = 0.5,
) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)

    y_true = np.stack([
        _build_label_vector(defect) for defect in test_df["defect"]
    ])
    y_pred_probs = model.predict(test_ds)
    y_pred = (y_pred_probs >= threshold).astype(int)

    # Classification report (precision/recall/F1 per defect label)
    report = classification_report(
        y_true, y_pred, target_names=DEFECT_LABELS, zero_division=0,
    )
    report_path = reports_dir / "classification_report.txt"
    report_path.write_text(report)
    print(f"\nClassification report saved -> {report_path}\n{report}")

    # Per-label confusion matrix grid
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    for i, label in enumerate(DEFECT_LABELS):
        ax = axes.flat[i]
        cm = confusion_matrix(y_true[:, i], y_pred[:, i])
        ax.imshow(cm, cmap="Blues")
        ax.set_title(label)
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")
        ax.set_xticks([0, 1])
        ax.set_yticks([0, 1])
        for r in range(cm.shape[0]):
            for c in range(cm.shape[1]):
                ax.text(c, r, str(cm[r, c]), ha="center", va="center",
                        color="white" if cm[r, c] > cm.max() / 2 else "black")
    fig.tight_layout()
    cm_path = reports_dir / "confusion_matrix.png"
    fig.savefig(cm_path, dpi=150)
    plt.close(fig)
    print(f"Confusion matrices saved -> {cm_path}")


def _build_label_vector(defect: str) -> np.ndarray:
    vec = np.zeros(len(DEFECT_LABELS), dtype=np.float32)
    if defect in DEFECT_LABELS:
        vec[DEFECT_LABELS.index(defect)] = 1.0
    return vec


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=str(BASE_DIR / "artifacts" / "model.keras"))
    parser.add_argument("--synthetic-dir", default=str(BASE_DIR / "synthetic_output"))
    args = parser.parse_args()

    model = tf.keras.models.load_model(args.model)
    df = load_manifest(Path(args.synthetic_dir))
    _, _, test_df = stratified_split(df)
    test_ds = dataframe_to_dataset(test_df, shuffle=False)

    evaluate_model(model, test_ds, test_df, BASE_DIR / "reports")
