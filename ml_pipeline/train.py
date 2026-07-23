"""
train.py — EfficientNetB0 Transfer Learning for Clothing Defect Detection
============================================================================
RUN THIS ON GOOGLE COLAB WITH A GPU RUNTIME (Runtime -> Change runtime type
-> T4 GPU, free tier is enough). Running it on a CPU-only machine will work
but will be dramatically slower (hours instead of minutes per epoch).

WHAT THIS SCRIPT DOES, IN ORDER:
  1. Loads the synthetic dataset produced by synthetic_data_generator.py
  2. Splits it into train/val/test (stratified by grade)
  3. Builds an EfficientNetB0 model (ImageNet pretrained, frozen backbone)
  4. Phase 1: trains only the new classification head
  5. Phase 2: unfreezes the top of the backbone and fine-tunes at low LR
  6. Evaluates on the held-out test set, saves accuracy/loss graphs,
     a classification report, and a confusion matrix per label
  7. Converts the trained model to TFLite and writes labels.txt + metadata.json
  8. Copies model.tflite + labels.txt into the backend so the API can use it

BEFORE RUNNING THIS FOR REAL:
  Replace the placeholder assets (see make_placeholder_assets.py) with real
  photographed clothing and real defect textures, then rerun
  synthetic_data_generator.py. Training on placeholder rectangles will
  produce a model that "works" on paper and is useless in practice — don't
  let that number end up in your report.
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # no display available in Colab/headless runs
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models, optimizers, callbacks

from augmentation import build_augmentation_pipeline
from dataset_preprocessing import (
    DEFECT_LABELS,
    IMAGE_SIZE,
    dataframe_to_dataset,
    load_manifest,
    stratified_split,
)

BASE_DIR = Path(__file__).parent
SYNTHETIC_OUTPUT_DIR = BASE_DIR / "synthetic_output"
ARTIFACTS_DIR = BASE_DIR / "artifacts"
REPORTS_DIR = BASE_DIR / "reports"
BACKEND_ARTIFACTS_DIR = BASE_DIR.parent / "backend" / "app" / "ml" / "artifacts"

BATCH_SIZE = 32
PHASE1_EPOCHS = 15   # frozen backbone, head only
PHASE2_EPOCHS = 10   # fine-tuning, top of backbone unfrozen
FINE_TUNE_AT_LAYER = 100  # unfreeze layers from this index onward (EfficientNetB0 has ~237)


def enable_mixed_precision_if_gpu_available() -> None:
    """Mixed precision (float16 compute, float32 storage) roughly doubles
    training speed on modern NVIDIA GPUs (Colab's T4 included) but gives no
    benefit — sometimes a slowdown — on CPU, so only turn it on when a GPU
    is actually present."""
    gpus = tf.config.list_physical_devices("GPU")
    if gpus:
        tf.keras.mixed_precision.set_global_policy("mixed_float16")
        print(f"Mixed precision enabled ({len(gpus)} GPU(s) detected).")
    else:
        print("No GPU detected — running in float32. This will be slow; "
              "use a Colab GPU runtime for the real training run.")


def build_model(num_labels: int) -> tuple[tf.keras.Model, tf.keras.Model]:
    """Returns (full_model, backbone) so train() can freeze/unfreeze the
    backbone directly for the two-phase training strategy."""
    backbone = tf.keras.applications.EfficientNetB0(
        include_top=False,
        weights="imagenet",
        input_shape=(*IMAGE_SIZE, 3),
        pooling="avg",
    )
    backbone.trainable = False  # Phase 1 starts frozen

    inputs = layers.Input(shape=(*IMAGE_SIZE, 3))
    x = build_augmentation_pipeline()(inputs)
    # EfficientNet expects inputs in [0, 255] scaled by its own preprocessing;
    # our tf.data pipeline already normalizes to [0, 1], so undo that here
    # rather than duplicating normalization logic in two places.
    x = layers.Rescaling(255.0)(x)
    x = tf.keras.applications.efficientnet.preprocess_input(x)
    x = backbone(x, training=False)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(128, activation="relu")(x)
    x = layers.Dropout(0.2)(x)
    outputs = layers.Dense(num_labels, activation="sigmoid", dtype="float32")(x)

    model = models.Model(inputs, outputs, name="rewear_defect_classifier")
    return model, backbone


def compile_model(model: tf.keras.Model, learning_rate: float) -> None:
    model.compile(
        optimizer=optimizers.Adam(learning_rate=learning_rate),
        loss="binary_crossentropy",
        metrics=[
            tf.keras.metrics.AUC(name="auc", multi_label=True),
            tf.keras.metrics.Precision(name="precision"),
            tf.keras.metrics.Recall(name="recall"),
        ],
    )


def get_callbacks(checkpoint_path: Path) -> list:
    return [
        callbacks.EarlyStopping(
            monitor="val_loss", patience=5, restore_best_weights=True,
        ),
        callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=3, min_lr=1e-6,
        ),
        callbacks.ModelCheckpoint(
            filepath=str(checkpoint_path), monitor="val_loss",
            save_best_only=True,
        ),
    ]


def plot_history(history_phase1, history_phase2, out_path: Path) -> None:
    acc = history_phase1.history.get("auc", []) + (history_phase2.history.get("auc", []) if history_phase2 else [])
    val_acc = history_phase1.history.get("val_auc", []) + (history_phase2.history.get("val_auc", []) if history_phase2 else [])
    loss = history_phase1.history.get("loss", []) + (history_phase2.history.get("loss", []) if history_phase2 else [])
    val_loss = history_phase1.history.get("val_loss", []) + (history_phase2.history.get("val_loss", []) if history_phase2 else [])
    phase_boundary = len(history_phase1.history.get("loss", []))

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    axes[0].plot(loss, label="train loss")
    axes[0].plot(val_loss, label="val loss")
    axes[0].axvline(phase_boundary, color="gray", linestyle="--", label="fine-tune start")
    axes[0].set_title("Loss")
    axes[0].set_xlabel("Epoch")
    axes[0].legend()

    axes[1].plot(acc, label="train AUC")
    axes[1].plot(val_acc, label="val AUC")
    axes[1].axvline(phase_boundary, color="gray", linestyle="--", label="fine-tune start")
    axes[1].set_title("AUC (multi-label)")
    axes[1].set_xlabel("Epoch")
    axes[1].legend()

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Training curves saved -> {out_path}")


def export_to_tflite(model: tf.keras.Model, num_train_samples: int, num_val_samples: int) -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    keras_path = ARTIFACTS_DIR / "model.keras"
    model.save(keras_path)
    print(f"Keras model saved -> {keras_path}")

    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_model = converter.convert()

    tflite_path = ARTIFACTS_DIR / "model.tflite"
    tflite_path.write_bytes(tflite_model)
    print(f"TFLite model saved -> {tflite_path} ({len(tflite_model) / 1e6:.2f} MB)")

    labels_path = ARTIFACTS_DIR / "labels.txt"
    labels_path.write_text("\n".join(DEFECT_LABELS))

    metadata = {
        "version": datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"),
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_model": "EfficientNetB0",
        "input_size": IMAGE_SIZE,
        "labels": DEFECT_LABELS,
        "num_train_samples": num_train_samples,
        "num_val_samples": num_val_samples,
    }
    (ARTIFACTS_DIR / "metadata.json").write_text(json.dumps(metadata, indent=2))

    # Wire it straight into the backend so /predict works immediately
    BACKEND_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy(tflite_path, BACKEND_ARTIFACTS_DIR / "model.tflite")
    shutil.copy(labels_path, BACKEND_ARTIFACTS_DIR / "labels.txt")
    shutil.copy(ARTIFACTS_DIR / "metadata.json", BACKEND_ARTIFACTS_DIR / "metadata.json")
    print(f"Model artifacts copied into backend -> {BACKEND_ARTIFACTS_DIR}")


def train(
    phase1_epochs: int = PHASE1_EPOCHS,
    phase2_epochs: int = PHASE2_EPOCHS,
    batch_size: int = BATCH_SIZE,
    quick_smoke_test: bool = False,
) -> None:
    """
    quick_smoke_test=True runs a tiny, fast version (few steps, 1-2 epochs
    per phase) purely to verify the code path has no bugs. It does NOT
    produce a usable model — use it only to sanity-check changes before
    committing to a full Colab run.
    """
    enable_mixed_precision_if_gpu_available()

    df = load_manifest(SYNTHETIC_OUTPUT_DIR)
    train_df, val_df, test_df = stratified_split(df)
    print(f"Train: {len(train_df)}  Val: {len(val_df)}  Test: {len(test_df)}")

    train_ds = dataframe_to_dataset(train_df, batch_size=batch_size, shuffle=True)
    val_ds = dataframe_to_dataset(val_df, batch_size=batch_size, shuffle=False)
    test_ds = dataframe_to_dataset(test_df, batch_size=batch_size, shuffle=False)

    if quick_smoke_test:
        train_ds = train_ds.take(2)
        val_ds = val_ds.take(1)
        phase1_epochs = min(phase1_epochs, 1)
        phase2_epochs = min(phase2_epochs, 1)

    model, backbone = build_model(num_labels=len(DEFECT_LABELS))
    compile_model(model, learning_rate=1e-3)
    model.summary()

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    checkpoint_path = ARTIFACTS_DIR / "checkpoint.keras"

    print("\n=== Phase 1: training classification head (backbone frozen) ===")
    history_phase1 = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=phase1_epochs,
        callbacks=get_callbacks(checkpoint_path),
    )

    print("\n=== Phase 2: fine-tuning top of backbone ===")
    backbone.trainable = True
    for layer in backbone.layers[:FINE_TUNE_AT_LAYER]:
        layer.trainable = False
    compile_model(model, learning_rate=1e-5)  # much lower LR for fine-tuning

    history_phase2 = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=phase2_epochs,
        callbacks=get_callbacks(checkpoint_path),
    )

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    plot_history(history_phase1, history_phase2, REPORTS_DIR / "training_curves.png")

    if not quick_smoke_test:
        from evaluate import evaluate_model
        evaluate_model(model, test_ds, test_df, REPORTS_DIR)

    export_to_tflite(model, num_train_samples=len(train_df), num_val_samples=len(val_df))


if __name__ == "__main__":
    import sys
    smoke_test = "--smoke-test" in sys.argv
    train(quick_smoke_test=smoke_test)
