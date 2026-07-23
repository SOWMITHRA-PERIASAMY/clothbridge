"""
Synthetic Defect Data Generator
--------------------------------
Generates labeled training images by compositing real defect textures
(stains, tears, holes) onto real clean clothing photos — NOT 3D rendering.

WHY THIS APPROACH (read before changing it):
Starting from real photographed clothing means there is no sim-to-real gap
to fight later: lighting, fabric wrinkles, and camera noise are already
real. We only synthesize the *defect*, which is the part that's genuinely
hard to collect at scale (nobody has thousands of photos of the same shirt
in every damage state).

FOLDER LAYOUT THIS SCRIPT EXPECTS:
  ml_pipeline/assets/clean_clothes/<category>/*.jpg
      e.g. assets/clean_clothes/jeans/jeans_01.jpg
      Put real, undamaged clothing photos here, organized by category.
  ml_pipeline/assets/defect_textures/<defect_type>/*.png
      e.g. assets/defect_textures/stain/coffee_01.png
      PNG with an alpha (transparency) channel — transparent everywhere
      except the stain/tear shape itself. See make_placeholder_assets.py
      for how to generate quick placeholder textures if you don't have
      real ones yet (useful to test the pipeline before sourcing real assets).

OUTPUT:
  ml_pipeline/synthetic_output/images/<uuid>.jpg   — the composited photo
  ml_pipeline/synthetic_output/labels/<uuid>.json  — what was done to it:
      {
        "category": "jeans",
        "defect": "stain",
        "severity": 0.42,
        "grade": "B",
        "bbox": [x, y, w, h],   <- exact location, since we placed it
        "source_clean_image": "jeans_01.jpg",
        "source_defect_texture": "coffee_01.png"
      }
  A manifest.csv is also written summarizing every generated sample, for
  quick class-balance checks before training.
"""
from __future__ import annotations

import json
import random
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path

import cv2
import numpy as np

BASE_DIR = Path(__file__).parent
CLEAN_DIR = BASE_DIR / "assets" / "clean_clothes"
DEFECT_DIR = BASE_DIR / "assets" / "defect_textures"
OUTPUT_IMAGES = BASE_DIR / "synthetic_output" / "images"
OUTPUT_LABELS = BASE_DIR / "synthetic_output" / "labels"
MANIFEST_PATH = BASE_DIR / "synthetic_output" / "manifest.csv"

DEFECT_TYPES = ["stain", "dirt", "tear", "hole", "fade"]
CATEGORIES = ["jeans", "shirt", "tshirt", "saree", "blanket", "curtain"]

# severity ranges per grade, matches app/services/quality_scoring.py logic
GRADE_SEVERITY_RANGES = {
    "A": (0.0, 0.0),     # clean, no defect at all
    "B": (0.10, 0.40),   # mild — repair/upcycle candidate
    "C": (0.40, 0.70),   # moderate — repair/upcycle, different suggestions
    "D": (0.70, 1.0),    # severe — reject/recycle
}


@dataclass
class GeneratedSample:
    sample_id: str
    category: str
    defect: str
    severity: float
    grade: str
    bbox: list  # [x, y, w, h] in pixels, or [] for clean/grade A
    source_clean_image: str
    source_defect_texture: str | None


def _list_images(directory: Path, exts=(".jpg", ".jpeg", ".png")) -> list[Path]:
    if not directory.exists():
        return []
    return [p for p in directory.iterdir() if p.suffix.lower() in exts]


def _load_rgb(path: Path) -> np.ndarray:
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Could not read image: {path}")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def _load_rgba(path: Path) -> np.ndarray:
    img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"Could not read texture: {path}")
    if img.shape[2] == 3:
        # no alpha channel provided — synthesize one from luminance
        # (assumes the texture image is on a plain white/black background)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        alpha = 255 - gray  # dark marks become opaque
        img = np.dstack([img, alpha])
    return cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)


def _grade_for_severity(severity: float) -> str:
    for grade, (lo, hi) in GRADE_SEVERITY_RANGES.items():
        if lo <= severity <= hi:
            return grade
    return "D"


def composite_defect(
    base_rgb: np.ndarray,
    defect_rgba: np.ndarray,
    severity: float,
) -> tuple[np.ndarray, list]:
    """Alpha-blends a defect texture onto the base image at a random
    position/scale/rotation, scaled in opacity by severity. Returns the
    resulting image and the exact [x, y, w, h] bbox where it was placed —
    this bbox becomes the ground-truth label, no manual annotation needed."""
    base_h, base_w = base_rgb.shape[:2]

    # scale the defect texture: bigger footprint for higher severity
    scale_factor = random.uniform(0.15, 0.30) * (0.5 + severity)
    target_w = max(10, int(base_w * scale_factor))
    aspect = defect_rgba.shape[0] / defect_rgba.shape[1]
    target_h = max(10, int(target_w * aspect))
    resized = cv2.resize(defect_rgba, (target_w, target_h), interpolation=cv2.INTER_AREA)

    # random rotation
    angle = random.uniform(0, 360)
    center = (target_w // 2, target_h // 2)
    rot_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        resized, rot_matrix, (target_w, target_h),
        borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0),
    )

    # random placement, fully inside the base image
    max_x = max(1, base_w - target_w)
    max_y = max(1, base_h - target_h)
    x = random.randint(0, max_x)
    y = random.randint(0, max_y)

    result = base_rgb.copy()
    defect_rgb = rotated[:, :, :3].astype(np.float32)
    alpha = (rotated[:, :, 3].astype(np.float32) / 255.0) * min(1.0, 0.4 + severity)
    alpha = alpha[:, :, None]

    roi = result[y:y + target_h, x:x + target_w].astype(np.float32)
    blended = roi * (1 - alpha) + defect_rgb * alpha
    result[y:y + target_h, x:x + target_w] = blended.astype(np.uint8)

    return result, [x, y, target_w, target_h]


def apply_fade(base_rgb: np.ndarray, severity: float) -> np.ndarray:
    """Fade isn't a pasted texture — it's a global desaturation/lightening,
    so it gets its own function rather than the compositing path above."""
    hsv = cv2.cvtColor(base_rgb, cv2.COLOR_RGB2HSV).astype(np.float32)
    hsv[:, :, 1] *= (1.0 - 0.6 * severity)   # reduce saturation
    hsv[:, :, 2] = np.clip(hsv[:, :, 2] * (1.0 + 0.25 * severity), 0, 255)  # slight lightening
    hsv = hsv.astype(np.uint8)
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)


def generate_dataset(
    samples_per_category_defect: int = 40,
    clean_samples_per_category: int = 20,
    seed: int = 42,
) -> list[GeneratedSample]:
    random.seed(seed)
    np.random.seed(seed)

    OUTPUT_IMAGES.mkdir(parents=True, exist_ok=True)
    OUTPUT_LABELS.mkdir(parents=True, exist_ok=True)

    generated: list[GeneratedSample] = []

    for category in CATEGORIES:
        clean_images = _list_images(CLEAN_DIR / category)
        if not clean_images:
            print(f"[skip] no clean images found for category '{category}' in "
                  f"{CLEAN_DIR / category} — add some and rerun.")
            continue

        # --- Grade A: clean, untouched ---
        for _ in range(clean_samples_per_category):
            src = random.choice(clean_images)
            base = _load_rgb(src)
            sample = _save_sample(base, category, "none", 0.0, "A", [], src.name, None)
            generated.append(sample)

        # --- Grades B/C/D: apply each defect type at varying severities ---
        for defect_type in DEFECT_TYPES:
            texture_files = _list_images(DEFECT_DIR / defect_type, exts=(".png",))
            if defect_type != "fade" and not texture_files:
                print(f"[skip] no textures found for defect '{defect_type}' in "
                      f"{DEFECT_DIR / defect_type} — add some and rerun.")
                continue

            for _ in range(samples_per_category_defect):
                src = random.choice(clean_images)
                base = _load_rgb(src)
                severity = random.uniform(0.10, 1.0)
                grade = _grade_for_severity(severity)

                if defect_type == "fade":
                    result = apply_fade(base, severity)
                    bbox: list = []
                    texture_name = None
                else:
                    texture_path = random.choice(texture_files)
                    defect_rgba = _load_rgba(texture_path)
                    result, bbox = composite_defect(base, defect_rgba, severity)
                    texture_name = texture_path.name

                sample = _save_sample(
                    result, category, defect_type, severity, grade,
                    bbox, src.name, texture_name,
                )
                generated.append(sample)

    _write_manifest(generated)
    print(f"\nGenerated {len(generated)} samples -> {OUTPUT_IMAGES}")
    print(f"Manifest written -> {MANIFEST_PATH}")
    return generated


def _save_sample(
    image_rgb: np.ndarray,
    category: str,
    defect: str,
    severity: float,
    grade: str,
    bbox: list,
    source_clean_image: str,
    source_defect_texture: str | None,
) -> GeneratedSample:
    sample_id = str(uuid.uuid4())
    image_path = OUTPUT_IMAGES / f"{sample_id}.jpg"
    label_path = OUTPUT_LABELS / f"{sample_id}.json"

    bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
    cv2.imwrite(str(image_path), bgr, [cv2.IMWRITE_JPEG_QUALITY, 90])

    sample = GeneratedSample(
        sample_id=sample_id,
        category=category,
        defect=defect,
        severity=round(severity, 3),
        grade=grade,
        bbox=bbox,
        source_clean_image=source_clean_image,
        source_defect_texture=source_defect_texture,
    )
    label_path.write_text(json.dumps(asdict(sample), indent=2))
    return sample


def _write_manifest(samples: list[GeneratedSample]) -> None:
    import csv
    with open(MANIFEST_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["sample_id", "category", "defect", "severity", "grade"])
        for s in samples:
            writer.writerow([s.sample_id, s.category, s.defect, s.severity, s.grade])


if __name__ == "__main__":
    generate_dataset()
