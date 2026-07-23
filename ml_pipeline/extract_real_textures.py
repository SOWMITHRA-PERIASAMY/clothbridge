"""
extract_real_textures.py
--------------------------
Turns a downloaded dataset of (photo, binary mask) pairs into transparent
PNG defect textures that drop straight into
ml_pipeline/assets/defect_textures/<defect_type>/ — the exact format
synthetic_data_generator.py already expects. No changes needed downstream.

WHY THIS MATTERS: the placeholder textures (make_placeholder_assets.py) are
drawn circles/blobs — fine for testing the pipeline, useless for a real
model. Datasets like stain_clothes(with-level) on Kaggle come with real
photographed stains AND a mask marking exactly where the stain is. This
script uses that mask to crop out just the stain pixels (with everything
else made transparent), so what you paste onto clean clothes later is a
real stain, not a drawn approximation.

EXPECTED INPUT LAYOUT (adjust to match whatever dataset you actually
download — check its folder structure first, this is the common pattern):
    <source_dataset>/images/<name>.jpg   — the original photo
    <source_dataset>/masks/<name>.png    — white (255) = defect region,
                                            black (0) = everything else

USAGE:
    python extract_real_textures.py \
        --images path/to/dataset/images \
        --masks path/to/dataset/masks \
        --defect-type stain \
        --output assets/defect_textures/stain
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np


def extract_texture(image_path: Path, mask_path: Path) -> np.ndarray | None:
    """Returns an RGBA crop of just the defect region, or None if the mask
    is empty (nothing to extract — some dataset entries are defect-free)."""
    image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)

    if image is None or mask is None:
        print(f"[skip] could not read {image_path.name} or its mask")
        return None

    if mask.shape[:2] != image.shape[:2]:
        mask = cv2.resize(mask, (image.shape[1], image.shape[0]))

    ys, xs = np.where(mask > 127)
    if len(xs) == 0:
        return None  # no defect region in this mask — nothing to extract

    # crop to the bounding box of the defect, with a small margin so blend
    # edges have room to feather
    margin = 5
    x0, x1 = max(0, xs.min() - margin), min(image.shape[1], xs.max() + margin)
    y0, y1 = max(0, ys.min() - margin), min(image.shape[0], ys.max() + margin)

    cropped_image = image[y0:y1, x0:x1]
    cropped_mask = mask[y0:y1, x0:x1]

    # feather the mask edge slightly so the paste doesn't look hard-cut
    alpha = cv2.GaussianBlur(cropped_mask, (5, 5), 0)

    rgba = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2BGRA)
    rgba[:, :, 3] = alpha
    return rgba


def run(images_dir: Path, masks_dir: Path, defect_type: str, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    image_files = sorted(images_dir.glob("*.*"))

    extracted = 0
    for image_path in image_files:
        mask_path = masks_dir / image_path.with_suffix(".png").name
        if not mask_path.exists():
            # try matching by stem in case extensions differ
            candidates = list(masks_dir.glob(f"{image_path.stem}.*"))
            if not candidates:
                continue
            mask_path = candidates[0]

        rgba = extract_texture(image_path, mask_path)
        if rgba is None:
            continue

        out_path = output_dir / f"{defect_type}_{image_path.stem}.png"
        cv2.imwrite(str(out_path), rgba)
        extracted += 1

    print(f"Extracted {extracted} real '{defect_type}' textures -> {output_dir}")
    if extracted == 0:
        print(
            "No textures extracted — check that --images and --masks point "
            "to matching files (same filenames, different folders/extensions)."
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--images", required=True, type=Path)
    parser.add_argument("--masks", required=True, type=Path)
    parser.add_argument("--defect-type", required=True, choices=["stain", "dirt", "tear", "hole"])
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    run(args.images, args.masks, args.defect_type, args.output)
