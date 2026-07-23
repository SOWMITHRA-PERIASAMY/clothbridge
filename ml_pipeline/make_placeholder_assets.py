"""
Placeholder Asset Generator — FOR TESTING THE PIPELINE ONLY.

These are simple procedurally-drawn shapes, not real clothing photos.
They exist so you (and I) can verify synthetic_data_generator.py actually
works end-to-end before you spend time sourcing real photos and textures.

DO NOT use output trained on these placeholders as a real model — swap
these folders for real clean-clothing photos and real defect texture PNGs
before running the actual training pipeline. This script will tell you
loudly if you try to skip that step (see train.py's asset check).
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

BASE_DIR = Path(__file__).parent
CLEAN_DIR = BASE_DIR / "assets" / "clean_clothes"
DEFECT_DIR = BASE_DIR / "assets" / "defect_textures"

CATEGORY_COLORS = {
    "jeans": (60, 90, 140),
    "shirt": (200, 200, 210),
    "tshirt": (180, 60, 60),
    "saree": (150, 40, 120),
    "blanket": (90, 130, 90),
    "curtain": (170, 150, 100),
}


def make_placeholder_clothing(n_per_category: int = 5, size=(400, 400)) -> None:
    for category, color in CATEGORY_COLORS.items():
        out_dir = CLEAN_DIR / category
        out_dir.mkdir(parents=True, exist_ok=True)
        for i in range(n_per_category):
            # base color with slight per-image variation + fabric-like noise texture
            variation = np.random.randint(-15, 15, 3)
            base_color = np.clip(np.array(color) + variation, 0, 255)
            img = np.ones((*size, 3), dtype=np.uint8) * base_color.astype(np.uint8)
            noise = np.random.normal(0, 6, (*size, 3)).astype(np.int16)
            img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
            path = out_dir / f"{category}_{i:02d}.jpg"
            cv2.imwrite(str(path), cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    print(f"Placeholder clean clothing images written under {CLEAN_DIR}")


def make_placeholder_defect_textures(n_per_defect: int = 4, size=(150, 150)) -> None:
    # stain / dirt: irregular dark blobs
    for defect, base_hue in [("stain", (40, 20, 10)), ("dirt", (60, 45, 30))]:
        out_dir = DEFECT_DIR / defect
        out_dir.mkdir(parents=True, exist_ok=True)
        for i in range(n_per_defect):
            rgba = np.zeros((*size, 4), dtype=np.uint8)
            center = (size[1] // 2, size[0] // 2)
            for _ in range(6):
                cx = center[0] + np.random.randint(-30, 30)
                cy = center[1] + np.random.randint(-30, 30)
                radius = np.random.randint(15, 45)
                color = tuple(int(c + np.random.randint(-10, 10)) for c in base_hue)
                cv2.circle(rgba, (cx, cy), radius, (*color, 255), -1)
            rgba[:, :, 3] = cv2.GaussianBlur(rgba[:, :, 3], (9, 9), 0)
            path = out_dir / f"{defect}_{i:02d}.png"
            cv2.imwrite(str(path), rgba)

    # tear / hole: irregular black opaque shapes (fully "removes" fabric visually)
    for defect in ["tear", "hole"]:
        out_dir = DEFECT_DIR / defect
        out_dir.mkdir(parents=True, exist_ok=True)
        for i in range(n_per_defect):
            rgba = np.zeros((*size, 4), dtype=np.uint8)
            pts = np.array([
                [size[1] // 2 + np.random.randint(-40, 40), size[0] // 2 + np.random.randint(-40, 40)]
                for _ in range(6)
            ])
            cv2.fillPoly(rgba, [pts], (10, 10, 10, 255))
            path = out_dir / f"{defect}_{i:02d}.png"
            cv2.imwrite(str(path), rgba)

    print(f"Placeholder defect textures written under {DEFECT_DIR}")


if __name__ == "__main__":
    make_placeholder_clothing()
    make_placeholder_defect_textures()
