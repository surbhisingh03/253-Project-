"""High-resolution figures for the presentation.

Numbers are read from the result CSVs or from one forward pass of the frozen
checkpoint on four already-generated test images. Nothing here is illustrative.
"""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch

from config import FIGURES, PERTURBED, RESULTS, YOLO_DIR

OUT = FIGURES / "slides"
NAVY = "#0B1F3A"
GREEN = "#1F8A4C"
RED = "#B42318"
INK = "#12202B"
MUTED = "#5C6B7A"
GOLD = "#C47B17"

CLASS_ORDER = [
    "missing_hole",
    "mouse_bite",
    "open_circuit",
    "short",
    "spur",
    "spurious_copper",
]
CLASS_LABEL = {
    "missing_hole": "Missing hole",
    "mouse_bite": "Mouse bite",
    "open_circuit": "Open circuit",
    "short": "Short",
    "spur": "Spur",
    "spurious_copper": "Spurious copper",
}


def style():
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 16,
            "axes.titlesize": 20,
            "axes.labelsize": 16,
            "xtick.labelsize": 15,
            "ytick.labelsize": 15,
            "axes.edgecolor": NAVY,
            "axes.labelcolor": INK,
            "xtick.color": INK,
            "ytick.color": INK,
            "text.color": INK,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )


def save(fig, name: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    fig.savefig(path, dpi=160, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    return path


def class_chart():
    report = json.loads((RESULTS / "dataset_report.json").read_text())
    counts = report["class_image_counts"]
    labels = [CLASS_LABEL[k] for k in CLASS_ORDER]
    values = [counts[k] for k in CLASS_ORDER]
    fig, ax = plt.subplots(figsize=(10.5, 5.6))
    bars = ax.bar(labels, values, color=GREEN, edgecolor=NAVY, width=0.72)
    ax.set_ylim(0, 150)
    ax.set_ylabel("Annotated images")
    ax.set_xlabel("")
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 3, str(value), ha="center", va="bottom", fontsize=16, color=NAVY, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    save(fig, "class_distribution.png")


def baseline_chart():
    row = pd.read_csv(RESULTS / "baseline_metrics.csv").iloc[0]
    detection = [
        ("Precision", float(row.precision), GREEN),
        ("Recall", float(row.recall), GREEN),
        ("F1", float(row.f1), GREEN),
        ("mAP@0.5", float(row.map50), GREEN),
    ]
    localization = [
        ("mAP@.5:.95", float(row.map50_95), NAVY),
        ("IoU of hits", float(row.mean_iou_tp), NAVY),
        ("False-neg. rate", float(row.false_negative_rate), RED),
    ]
    items = detection + localization
    fig, ax = plt.subplots(figsize=(11.2, 5.8))
    xs = np.arange(len(items))
    bars = ax.bar(xs, [v for _, v, _ in items], color=[c for _, _, c in items], edgecolor=NAVY, width=0.72)
    ax.set_xticks(xs)
    ax.set_xticklabels([n for n, _, _ in items])
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("Score")
    ax.axhline(0.897, color=MUTED, linestyle="--", linewidth=1)
    for bar, (_, value, _) in zip(bars, items):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.03, f"{value:.3f}", ha="center", fontsize=14, color=NAVY, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    save(fig, "baseline_scores.png")


def recall_chart():
    frame = pd.read_csv(RESULTS / "perturbation_metrics.csv")
    base = float(pd.read_csv(RESULTS / "baseline_metrics.csv").iloc[0].recall)
    show = [
        ("gaussian_noise", "Noise", RED),
        ("localized_occlusion", "Occlusion", "#7A1F1F"),
        ("rotation", "Rotation", GOLD),
        ("gaussian_blur", "Blur", GREEN),
        ("jpeg", "JPEG", "#1D4E89"),
        ("brightness", "Brightness", "#5B7C99"),
    ]
    fig, ax = plt.subplots(figsize=(11.4, 6.2))
    ax.axhline(base, color=NAVY, linestyle="--", linewidth=1.6)
    ax.text(0.88, base + 0.035, f"Clean {base:.3f}", color=NAVY, fontsize=14, fontweight="bold")
    ends = []
    for key, label, color in show:
        part = frame[frame.perturbation == key].sort_values("level")
        ys = part.recall.to_numpy()
        ax.plot([1, 2, 3], ys, marker="o", markersize=9, linewidth=2.6, color=color)
        ends.append((float(ys[-1]), label, color))
    ends.sort()
    placed = []
    for y, label, color in ends:
        target = y
        for previous in placed:
            if abs(target - previous) < 0.055:
                target = previous + 0.055
        placed.append(target)
        ax.annotate(
            label,
            xy=(3, y),
            xytext=(3.12, target),
            color=color,
            fontsize=14,
            fontweight="bold",
            va="center",
            arrowprops=dict(arrowstyle="-", color=color, lw=0.8) if abs(target - y) > 0.03 else None,
        )
    ax.set_xlim(0.8, 4.15)
    ax.set_ylim(-0.02, 1.08)
    ax.set_xticks([1, 2, 3])
    ax.set_xticklabels(["Level 1\nmild", "Level 2", "Level 3\nstrongest"])
    ax.set_ylabel("Recall")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    save(fig, "recall_lines.png")


def heatmap():
    per = pd.read_csv(RESULTS / "perturbation_per_class.csv")
    base = pd.read_csv(RESULTS / "per_class_metrics.csv").set_index("class_name")
    columns = [
        ("Clean", None, None),
        ("Noise\nσ = 25", "gaussian_noise", 2),
        ("Cover\n~30% area", "localized_occlusion", 2),
        ("Rotation\n12°", "rotation", 3),
    ]
    matrix = []
    for name in CLASS_ORDER:
        row = [float(base.loc[name, "recall"])]
        for _, family, level in columns[1:]:
            hit = per[(per.class_name == name) & (per.perturbation == family) & (per.level == level)]
            row.append(float(hit.recall.iloc[0]))
        matrix.append(row)
    data = np.array(matrix)
    fig, ax = plt.subplots(figsize=(10.8, 6.0))
    image = ax.imshow(data, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(columns)))
    ax.set_xticklabels([c[0] for c in columns], fontsize=15)
    ax.set_yticks(range(len(CLASS_ORDER)))
    ax.set_yticklabels([CLASS_LABEL[c] for c in CLASS_ORDER], fontsize=16)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            value = data[i, j]
            ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=16, color="white" if value < 0.45 else NAVY, fontweight="bold")
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04).set_label("Recall", fontsize=14)
    fig.tight_layout()
    save(fig, "class_heatmap.png")


def read_yolo(path: Path, width: int, height: int):
    boxes = []
    if not path.exists():
        return boxes
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        cls, x, y, w, h = line.split()
        x, y, w, h = map(float, (x, y, w, h))
        boxes.append(
            {
                "cls": int(cls),
                "xmin": (x - w / 2) * width,
                "ymin": (y - h / 2) * height,
                "xmax": (x + w / 2) * width,
                "ymax": (y + h / 2) * height,
            }
        )
    return boxes


def iou(a, b) -> float:
    x1, y1 = max(a["xmin"], b["xmin"]), max(a["ymin"], b["ymin"])
    x2, y2 = min(a["xmax"], b["xmax"]), min(a["ymax"], b["ymax"])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    if inter <= 0:
        return 0.0
    area_a = (a["xmax"] - a["xmin"]) * (a["ymax"] - a["ymin"])
    area_b = (b["xmax"] - b["xmin"]) * (b["ymax"] - b["ymin"])
    return inter / (area_a + area_b - inter)


def crop_around(image, box, pad=150):
    h, w = image.shape[:2]
    x1 = int(max(0, box["xmin"] - pad))
    y1 = int(max(0, box["ymin"] - pad))
    x2 = int(min(w, box["xmax"] + pad))
    y2 = int(min(h, box["ymax"] + pad))
    return image[y1:y2, x1:x2].copy(), x1, y1


def draw_boxes(image, gt, preds, origin):
    ox, oy = origin
    canvas = image.copy()
    for box in gt:
        p1 = (int(box["xmin"] - ox), int(box["ymin"] - oy))
        p2 = (int(box["xmax"] - ox), int(box["ymax"] - oy))
        cv2.rectangle(canvas, p1, p2, (31, 138, 76), 2)
    for box in preds:
        p1 = (int(box["xmin"] - ox), int(box["ymin"] - oy))
        p2 = (int(box["xmax"] - ox), int(box["ymax"] - oy))
        cv2.rectangle(canvas, p1, p2, (36, 35, 180), 2)
        label = f"{box['conf']:.2f}"
        cv2.putText(canvas, label, (p1[0], max(16, p1[1] - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (36, 35, 180), 2, cv2.LINE_AA)
    return canvas


def predict(model, path: Path):
    result = model.predict(source=str(path), conf=0.25, iou=0.45, imgsz=640, verbose=False)[0]
    boxes = []
    if result.boxes is None:
        return boxes
    for xyxy, conf, cls in zip(result.boxes.xyxy.cpu().numpy(), result.boxes.conf.cpu().numpy(), result.boxes.cls.cpu().numpy()):
        boxes.append({"xmin": float(xyxy[0]), "ymin": float(xyxy[1]), "xmax": float(xyxy[2]), "ymax": float(xyxy[3]), "conf": float(conf), "cls": int(cls)})
    return boxes


def comparison_panels():
    from ultralytics import YOLO

    stem = "missing_hole__01_missing_hole_09"
    original_path = YOLO_DIR / "images" / "test" / f"{stem}.jpg"
    specs = [
        ("Original", original_path, YOLO_DIR / "labels" / "test" / f"{stem}.txt", "none"),
        ("Noise, σ = 25", PERTURBED / "gaussian_noise" / "level2" / "images" / f"{stem}.jpg", PERTURBED / "gaussian_noise" / "level2" / "labels" / f"{stem}.txt", "noise"),
        ("Rotation, 12°", PERTURBED / "rotation" / "level3" / "images" / f"{stem}.jpg", PERTURBED / "rotation" / "level3" / "labels" / f"{stem}.txt", "rotation"),
        ("Cover, side 0.55", PERTURBED / "localized_occlusion" / "level2" / "images" / f"{stem}.jpg", PERTURBED / "localized_occlusion" / "level2" / "labels" / f"{stem}.txt", "occlusion"),
    ]
    model = YOLO(str(RESULTS / "best.pt"))
    image0 = cv2.imread(str(original_path))
    h, w = image0.shape[:2]
    gt0 = read_yolo(YOLO_DIR / "labels" / "test" / f"{stem}.txt", w, h)
    focus_index = sorted(range(len(gt0)), key=lambda i: gt0[i]["ymin"])[1]
    focus = gt0[focus_index]
    records = []
    OUT.mkdir(parents=True, exist_ok=True)
    for title, image_path, label_path, key in specs:
        image = cv2.imread(str(image_path))
        hh, ww = image.shape[:2]
        gt = read_yolo(label_path, ww, hh)
        # Pair with the original focus by order when the transform keeps the box.
        if key == "none":
            target = focus
        else:
            target = gt[focus_index] if focus_index < len(gt) else gt[0]
        preds = predict(model, image_path)
        matched = [p for p in preds if p["cls"] == target["cls"] and iou(p, target) >= 0.5]
        matched.sort(key=lambda p: p["conf"], reverse=True)
        crop, ox, oy = crop_around(image, target, pad=160)
        panel = draw_boxes(crop, [target], [p for p in preds if p["xmax"] > ox and p["xmin"] < ox + crop.shape[1] and p["ymax"] > oy and p["ymin"] < oy + crop.shape[0]], (ox, oy))
        out = OUT / f"panel_{key}.jpg"
        cv2.imwrite(str(out), panel, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
        if matched:
            result = f"Detected {matched[0]['conf']:.2f}"
        else:
            result = "Missed"
        records.append({"key": key, "title": title, "result": result, "file": out.name, "n_pred_on_image": len(preds), "n_gt": len(gt)})
    # Full-board view with one highlighted hole for the decision slide.
    board = image0.copy()
    p1 = (int(focus["xmin"]), int(focus["ymin"]))
    p2 = (int(focus["xmax"]), int(focus["ymax"]))
    cv2.rectangle(board, p1, p2, (36, 35, 180), 6)
    crop, _, _ = crop_around(board, focus, pad=280)
    cv2.imwrite(str(OUT / "decision_crop.jpg"), crop, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    cv2.imwrite(str(OUT / "title_crop.jpg"), crop_around(image0, focus, pad=220)[0], [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    (OUT / "panel_results.json").write_text(json.dumps(records, indent=2))
    print(json.dumps(records, indent=2))


def class_examples():
    OUT.mkdir(parents=True, exist_ok=True)
    test_images = YOLO_DIR / "images" / "test"
    test_labels = YOLO_DIR / "labels" / "test"
    chosen = {}
    for image_path in sorted(test_images.glob("*.jpg")):
        label = test_labels / f"{image_path.stem}.txt"
        image = cv2.imread(str(image_path))
        if image is None:
            continue
        h, w = image.shape[:2]
        boxes = read_yolo(label, w, h)
        if not boxes:
            continue
        cls = boxes[0]["cls"]
        name = CLASS_ORDER[cls]
        if name in chosen:
            continue
        box = max(boxes, key=lambda b: (b["xmax"] - b["xmin"]) * (b["ymax"] - b["ymin"]))
        crop, ox, oy = crop_around(image, box, pad=90)
        cv2.rectangle(
            crop,
            (int(box["xmin"] - ox), int(box["ymin"] - oy)),
            (int(box["xmax"] - ox), int(box["ymax"] - oy)),
            (31, 138, 76),
            2,
        )
        cv2.imwrite(str(OUT / f"class_{name}.jpg"), crop, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
        chosen[name] = image_path.name
        if len(chosen) == 6:
            break
    (OUT / "class_examples.json").write_text(json.dumps(chosen, indent=2))


def main():
    style()
    class_chart()
    baseline_chart()
    recall_chart()
    heatmap()
    class_examples()
    comparison_panels()


if __name__ == "__main__":
    main()
