"""
generate_tear_hole_textures.py
---------------------------------
Procedurally generates realistic tear/hole textures for compositing.

WHY PROCEDURAL, NOT DATASET-SOURCED (unlike stains):
A tear or hole is fabric that is physically missing, with frayed thread
edges — a shape/geometry problem, not a color/texture problem the way a
stain is. Public fabric-defect datasets we checked either don't include
usable per-defect masks for this (see fabric-defects-dataset's "hole"
category — that's industrial pinhole/anomaly speckling across a whole
roll, not a single visible tear) or only exist at resolutions too small
to be useful (32x32 MVTec-style crops). Generating a well-designed
irregular shape with frayed edges is the more defensible choice here,
and is documented as a deliberate decision, not a shortcut.

This produces:
  - Jagged, irregular hole/tear outlines (not simple circles/polygons)
  - Frayed edge threads radiating from the tear boundary
  - Dark interior (what's visible through/behind the hole) with soft
    inner shadow near the edges, since real tears show depth, not a flat
    black cutout
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

BASE_DIR = Path(__file__).parent
OUTPUT_DIRS = {
    "tear": BASE_DIR / "assets" / "defect_textures" / "tear",
    "hole": BASE_DIR / "assets" / "defect_textures" / "hole",
}


def _irregular_polygon(center, radius, n_points, jaggedness, rng):
    angles = np.sort(rng.uniform(0, 2 * np.pi, n_points))
    radii = radius * (1 + rng.uniform(-jaggedness, jaggedness, n_points))
    xs = center[0] + radii * np.cos(angles)
    ys = center[1] + radii * np.sin(angles)
    return np.stack([xs, ys], axis=1).astype(np.int32)


def _draw_frayed_edges(canvas_alpha, polygon, rng, n_threads=18, thread_length_frac=0.18):
    """Radiating thin lines just outside the tear boundary, mimicking loose
    frayed threads — the visual detail that makes a hole read as fabric
    damage rather than a clean die-cut shape."""
    center = polygon.mean(axis=0)
    max_dim = max(canvas_alpha.shape)
    for i in range(n_threads):
        idx = rng.integers(0, len(polygon))
        point = polygon[idx]
        direction = point - center
        norm = np.linalg.norm(direction)
        if norm == 0:
            continue
        direction = direction / norm
        length = max_dim * thread_length_frac * rng.uniform(0.5, 1.0)
        end_point = point + direction * length
        # slight wobble so threads don't look perfectly straight
        mid_point = point + direction * length * 0.5 + rng.uniform(-4, 4, 2)
        pts = np.array([point, mid_point, end_point], dtype=np.int32)
        thickness = rng.integers(1, 3)
        alpha_val = int(rng.uniform(90, 180))
        cv2.polylines(canvas_alpha, [pts], isClosed=False, color=alpha_val, thickness=thickness)


def generate_one(size=(180, 180), seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    h, w = size
    canvas = np.zeros((h, w, 4), dtype=np.uint8)

    center = np.array([w / 2 + rng.uniform(-10, 10), h / 2 + rng.uniform(-10, 10)])
    radius = min(h, w) * rng.uniform(0.18, 0.32)
    n_points = rng.integers(9, 15)
    jaggedness = rng.uniform(0.15, 0.35)

    polygon = _irregular_polygon(center, radius, n_points, jaggedness, rng)

    # interior: near-black with slight variation, simulating the dark gap
    # where fabric is missing (what shows through/behind the garment)
    interior_alpha = np.zeros((h, w), dtype=np.uint8)
    cv2.fillPoly(interior_alpha, [polygon], 255)
    interior_alpha = cv2.GaussianBlur(interior_alpha, (5, 5), 0)

    interior_color = np.full((h, w, 3), rng.integers(5, 25), dtype=np.uint8)
    canvas[:, :, :3] = interior_color
    canvas[:, :, 3] = interior_alpha

    # frayed thread detail just outside the main hole boundary
    thread_alpha = np.zeros((h, w), dtype=np.uint8)
    _draw_frayed_edges(thread_alpha, polygon, rng)
    thread_layer_color = np.full((h, w, 3), rng.integers(60, 100), dtype=np.uint8)  # thread-ish gray

    # composite thread layer under/around the main hole (max-alpha combine)
    combined_alpha = np.maximum(canvas[:, :, 3], thread_alpha)
    thread_mask = thread_alpha > canvas[:, :, 3]
    canvas[thread_mask, :3] = thread_layer_color[thread_mask]
    canvas[:, :, 3] = combined_alpha

    return canvas


def generate_set(defect_type: str, n: int = 30) -> None:
    out_dir = OUTPUT_DIRS[defect_type]
    out_dir.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        img = generate_one(seed=hash((defect_type, i)) % (2**31))
        cv2.imwrite(str(out_dir / f"{defect_type}_{i:03d}.png"), img)
    print(f"Generated {n} '{defect_type}' textures -> {out_dir}")


if __name__ == "__main__":
    generate_set("tear", n=30)
    generate_set("hole", n=30)
