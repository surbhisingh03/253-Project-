"""Create controlled test-image perturbations.

Photometric changes keep the original boxes. Geometric changes write transformed
boxes. Localized occlusion covers part of each annotated defect and keeps the
original box, because the audit asks whether the detector still finds a defect
that remains in the annotation. Original test images are never modified.
"""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from PIL import Image

from calculate_metrics import load_yolo_labels
from config import CLASSES, PERTURBED, RESULTS, YOLO_DIR

SPECS = [
    ("brightness", [-40, 40, 80], "intensity_offset"),
    ("contrast", [0.6, 0.8, 1.4], "alpha"),
    ("gaussian_blur", [3, 9, 15], "kernel"),
    ("gaussian_noise", [10, 25, 40], "sigma"),
    ("jpeg", [75, 40, 15], "quality"),
    ("rotation", [3, 7, 12], "degrees"),
    ("scale", [0.85, 1.15, 1.30], "scale"),
    ("illumination", [0.25, 0.45, 0.65], "gradient_strength"),
    ("localized_occlusion", [0.30, 0.55, 0.80], "box_side_fraction"),
]


def read_bgr(path: Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(path)
    return image


def clip_uint8(image: np.ndarray) -> np.ndarray:
    return np.clip(image, 0, 255).astype(np.uint8)


def apply_brightness(image: np.ndarray, delta: float) -> np.ndarray:
    return clip_uint8(image.astype(np.float32) + delta)


def apply_contrast(image: np.ndarray, alpha: float) -> np.ndarray:
    mean = image.astype(np.float32).mean(axis=(0, 1), keepdims=True)
    return clip_uint8((image.astype(np.float32) - mean) * alpha + mean)


def apply_blur(image: np.ndarray, kernel: int) -> np.ndarray:
    k = int(kernel) | 1
    return cv2.GaussianBlur(image, (k, k), 0)


def apply_noise(image: np.ndarray, sigma: float, rng: np.random.Generator) -> np.ndarray:
    noise = rng.normal(0, sigma, image.shape)
    return clip_uint8(image.astype(np.float32) + noise)


def apply_jpeg(image: np.ndarray, quality: int) -> np.ndarray:
    ok, encoded = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
    if not ok:
        raise RuntimeError("JPEG encode failed")
    return cv2.imdecode(encoded, cv2.IMREAD_COLOR)


def apply_illumination(image: np.ndarray, strength: float) -> np.ndarray:
    height, width = image.shape[:2]
    ramp = np.linspace(1 - strength, 1 + strength, width, dtype=np.float32)
    return clip_uint8(image.astype(np.float32) * ramp[None, :, None])


def transform_points(points: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    homogeneous = np.concatenate([points, np.ones((len(points), 1))], axis=1)
    return (matrix @ homogeneous.T).T


def rotate_image_and_boxes(image: np.ndarray, boxes: list[dict], angle: float):
    height, width = image.shape[:2]
    matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1.0)
    rotated = cv2.warpAffine(
        image, matrix, (width, height), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101
    )
    new_boxes = []
    for box in boxes:
        corners = np.array(
            [
                [box["xmin"], box["ymin"]],
                [box["xmax"], box["ymin"]],
                [box["xmax"], box["ymax"]],
                [box["xmin"], box["ymax"]],
            ],
            dtype=float,
        )
        mapped = transform_points(corners, matrix)
        xmin, ymin = mapped.min(axis=0)
        xmax, ymax = mapped.max(axis=0)
        xmin, ymin = max(0, xmin), max(0, ymin)
        xmax, ymax = min(width - 1, xmax), min(height - 1, ymax)
        if xmax - xmin < 2 or ymax - ymin < 2:
            continue
        new_boxes.append({**box, "xmin": xmin, "ymin": ymin, "xmax": xmax, "ymax": ymax})
    return rotated, new_boxes


def scale_image_and_boxes(image: np.ndarray, boxes: list[dict], scale: float):
    height, width = image.shape[:2]
    resized = cv2.resize(image, (int(round(width * scale)), int(round(height * scale))), interpolation=cv2.INTER_LINEAR)
    canvas = np.full_like(image, 114)
    rh, rw = resized.shape[:2]
    if scale >= 1:
        x0 = max(0, (rw - width) // 2)
        y0 = max(0, (rh - height) // 2)
        canvas[:, :] = resized[y0 : y0 + height, x0 : x0 + width]
        ox, oy = -x0, -y0
    else:
        x0 = (width - rw) // 2
        y0 = (height - rh) // 2
        canvas[y0 : y0 + rh, x0 : x0 + rw] = resized
        ox, oy = x0, y0
    new_boxes = []
    for box in boxes:
        xmin = box["xmin"] * scale + ox
        xmax = box["xmax"] * scale + ox
        ymin = box["ymin"] * scale + oy
        ymax = box["ymax"] * scale + oy
        xmin, ymin = max(0, xmin), max(0, ymin)
        xmax, ymax = min(width - 1, xmax), min(height - 1, ymax)
        if xmax - xmin < 2 or ymax - ymin < 2:
            continue
        new_boxes.append({**box, "xmin": float(xmin), "ymin": float(ymin), "xmax": float(xmax), "ymax": float(ymax)})
    return canvas, new_boxes


def apply_occlusion(image: np.ndarray, boxes: list[dict], fraction: float) -> np.ndarray:
    out = image.copy()
    for box in boxes:
        bw = box["xmax"] - box["xmin"]
        bh = box["ymax"] - box["ymin"]
        cw = bw * fraction
        ch = bh * fraction
        cx = (box["xmin"] + box["xmax"]) / 2
        cy = (box["ymin"] + box["ymax"]) / 2
        x1 = int(round(max(0, cx - cw / 2)))
        y1 = int(round(max(0, cy - ch / 2)))
        x2 = int(round(min(image.shape[1] - 1, cx + cw / 2)))
        y2 = int(round(min(image.shape[0] - 1, cy + ch / 2)))
        if x2 <= x1 or y2 <= y1:
            continue
        out[y1:y2, x1:x2] = (128, 128, 128)
    return out


def write_labels(path: Path, boxes: list[dict], width: int, height: int) -> None:
    lines = []
    for box in boxes:
        cls_id = box["class_id"]
        x = ((box["xmin"] + box["xmax"]) / 2) / width
        y = ((box["ymin"] + box["ymax"]) / 2) / height
        w = (box["xmax"] - box["xmin"]) / width
        h = (box["ymax"] - box["ymin"]) / height
        lines.append(f"{cls_id} {x:.6f} {y:.6f} {w:.6f} {h:.6f}")
    path.write_text("\n".join(lines) + ("\n" if lines else ""))


def main() -> int:
    image_dir = YOLO_DIR / "images" / "test"
    label_dir = YOLO_DIR / "labels" / "test"
    images = sorted(image_dir.glob("*.jpg"))
    if not images:
        raise SystemExit("No test images. Run prepare_dataset.py first.")
    if PERTURBED.exists():
        import shutil

        shutil.rmtree(PERTURBED)
    catalog = []
    rng = np.random.default_rng(253)
    for image_path in images:
        with Image.open(image_path) as image:
            width, height = image.size
        boxes = load_yolo_labels(label_dir / f"{image_path.stem}.txt", width, height)
        original = read_bgr(image_path)
        for family, levels, unit in SPECS:
            for level_index, intensity in enumerate(levels, start=1):
                folder = PERTURBED / family / f"level{level_index}"
                (folder / "images").mkdir(parents=True, exist_ok=True)
                (folder / "labels").mkdir(parents=True, exist_ok=True)
                changed_boxes = boxes
                if family == "brightness":
                    perturbed = apply_brightness(original, intensity)
                elif family == "contrast":
                    perturbed = apply_contrast(original, intensity)
                elif family == "gaussian_blur":
                    perturbed = apply_blur(original, intensity)
                elif family == "gaussian_noise":
                    perturbed = apply_noise(original, intensity, rng)
                elif family == "jpeg":
                    perturbed = apply_jpeg(original, intensity)
                elif family == "rotation":
                    perturbed, changed_boxes = rotate_image_and_boxes(original, boxes, intensity)
                elif family == "scale":
                    perturbed, changed_boxes = scale_image_and_boxes(original, boxes, intensity)
                elif family == "illumination":
                    perturbed = apply_illumination(original, intensity)
                elif family == "localized_occlusion":
                    perturbed = apply_occlusion(original, boxes, intensity)
                else:
                    raise ValueError(family)
                out_image = folder / "images" / image_path.name
                cv2.imwrite(str(out_image), perturbed)
                write_labels(folder / "labels" / f"{image_path.stem}.txt", changed_boxes, width, height)
                catalog.append(
                    {
                        "image_id": image_path.stem,
                        "perturbation": family,
                        "level": level_index,
                        "intensity": intensity,
                        "unit": unit,
                        "image_path": str(out_image.relative_to(PERTURBED.parent.parent)),
                        "n_boxes": len(changed_boxes),
                    }
                )
    frame = pd.DataFrame(catalog)
    RESULTS.mkdir(parents=True, exist_ok=True)
    frame.to_csv(RESULTS / "perturbation_catalog.csv", index=False)
    summary = {
        "n_source_images": len(images),
        "n_perturbed_images": int(len(frame)),
        "families": [row[0] for row in SPECS],
        "note": "Generated only from the held-out test split. Training images were not perturbed.",
    }
    (RESULTS / "perturbation_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
