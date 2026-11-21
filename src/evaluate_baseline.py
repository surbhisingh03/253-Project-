"""Run the frozen detector on original test images and write baseline metrics."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd
from PIL import Image

from calculate_metrics import (
    load_yolo_labels,
    mean_average_precision,
    operating_point,
    summarize_counts,
)
from config import (
    CLASSES,
    CONF_THRESHOLD,
    IMAGE_SIZE,
    MAP_CONF,
    MAX_DET,
    NMS_IOU,
    RESULTS,
    TABLES,
    YOLO_DIR,
)
from train_or_load_model import select_device


def predict_image(model, image_path: Path, device: str) -> tuple[list[dict], float]:
    started = time.perf_counter()
    results = model.predict(
        source=str(image_path),
        conf=MAP_CONF,
        iou=NMS_IOU,
        imgsz=IMAGE_SIZE,
        max_det=MAX_DET,
        device=device,
        verbose=False,
    )
    elapsed = time.perf_counter() - started
    detections = []
    if not results:
        return detections, elapsed
    result = results[0]
    if result.boxes is None or len(result.boxes) == 0:
        return detections, elapsed
    xyxy = result.boxes.xyxy.cpu().numpy()
    conf = result.boxes.conf.cpu().numpy()
    cls = result.boxes.cls.cpu().numpy().astype(int)
    for box, score, class_id in zip(xyxy, conf, cls):
        detections.append(
            {
                "class_id": int(class_id),
                "class_name": CLASSES[int(class_id)],
                "confidence": float(score),
                "xmin": float(box[0]),
                "ymin": float(box[1]),
                "xmax": float(box[2]),
                "ymax": float(box[3]),
            }
        )
    detections.sort(key=lambda row: row["confidence"], reverse=True)
    return detections, elapsed


def class_rows(image_id: str, ground_truth: list[dict], detections: list[dict]) -> list[dict]:
    rows = []
    for class_id, name in enumerate(CLASSES):
        gt = [g for g in ground_truth if g["class_id"] == class_id]
        det = [d for d in detections if d["class_id"] == class_id]
        stats = operating_point(gt, det)
        stats.update({"image_id": image_id, "class_name": name})
        rows.append(stats)
    return rows


def confusion_rows(image_id: str, ground_truth: list[dict], detections: list[dict]) -> list[dict]:
    from calculate_metrics import match_detections

    kept = [d for d in detections if d["confidence"] >= CONF_THRESHOLD]
    kept = sorted(kept, key=lambda d: d["confidence"], reverse=True)
    pairs, used_gt, used_det = match_detections(ground_truth, kept, class_aware=False)
    rows = []
    for gt_index, det_index, iou in pairs:
        rows.append(
            {
                "image_id": image_id,
                "gt_class": ground_truth[gt_index]["class_name"],
                "pred_class": kept[det_index]["class_name"],
                "iou": iou,
                "confidence": kept[det_index]["confidence"],
                "outcome": "matched",
            }
        )
    for gt_index, gt in enumerate(ground_truth):
        if gt_index not in used_gt:
            rows.append(
                {
                    "image_id": image_id,
                    "gt_class": gt["class_name"],
                    "pred_class": "missed",
                    "iou": 0.0,
                    "confidence": 0.0,
                    "outcome": "false_negative",
                }
            )
    for det_index, det in enumerate(kept):
        if det_index not in used_det:
            rows.append(
                {
                    "image_id": image_id,
                    "gt_class": "none",
                    "pred_class": det["class_name"],
                    "iou": 0.0,
                    "confidence": det["confidence"],
                    "outcome": "false_positive",
                }
            )
    return rows


def main() -> int:
    from ultralytics import YOLO

    weights = RESULTS / "best.pt"
    if not weights.exists():
        raise SystemExit("Missing results/best.pt. Run train_or_load_model.py first.")
    device = select_device()
    model = YOLO(str(weights))
    image_dir = YOLO_DIR / "images" / "test"
    label_dir = YOLO_DIR / "labels" / "test"
    images = sorted(image_dir.glob("*.jpg"))
    if not images:
        raise SystemExit("No test images found.")

    per_image = []
    per_class = []
    confusion = []
    all_gt = []
    all_det = []
    times = []
    for index, image_path in enumerate(images):
        with Image.open(image_path) as image:
            width, height = image.size
        ground_truth = load_yolo_labels(label_dir / f"{image_path.stem}.txt", width, height)
        detections, elapsed = predict_image(model, image_path, device)
        if index == 0:
            elapsed = None  # drop the first call, which includes warmup
        else:
            times.append(elapsed)
        stats = operating_point(ground_truth, detections)
        stats["image_id"] = image_path.stem
        stats["condition"] = "baseline"
        stats["perturbation"] = "none"
        stats["level"] = 0
        stats["intensity"] = 0.0
        per_image.append(stats)
        per_class.extend(class_rows(image_path.stem, ground_truth, detections))
        confusion.extend(confusion_rows(image_path.stem, ground_truth, detections))
        all_gt.append(ground_truth)
        all_det.append(detections)

    image_frame = pd.DataFrame(per_image)
    class_frame = pd.DataFrame(per_class)
    summary = summarize_counts(image_frame)
    maps = mean_average_precision(all_gt, all_det)
    summary.update(maps)
    summary["mean_inference_ms"] = float(sum(times) / len(times) * 1000) if times else None
    summary["conf_threshold"] = CONF_THRESHOLD
    summary["match_iou"] = 0.50
    summary["n_images"] = len(images)
    summary["device"] = device
    summary["status"] = "measured"

    RESULTS.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    image_frame.to_csv(RESULTS / "baseline_per_image.csv", index=False)
    class_frame.to_csv(RESULTS / "baseline_per_class_image.csv", index=False)
    pd.DataFrame(confusion).to_csv(RESULTS / "baseline_confusion_long.csv", index=False)

    class_summary = []
    for name in CLASSES:
        part = class_frame[class_frame["class_name"] == name]
        row = summarize_counts(part)
        row["class_name"] = name
        row["ap50"] = maps["per_class_ap50"].get(name)
        class_summary.append(row)
    class_summary_frame = pd.DataFrame(class_summary)
    class_summary_frame.to_csv(RESULTS / "per_class_metrics.csv", index=False)
    class_summary_frame.to_csv(TABLES / "baseline_per_class.csv", index=False)

    flat = {k: v for k, v in summary.items() if k != "per_class_ap50"}
    for name, ap in maps["per_class_ap50"].items():
        flat[f"ap50_{name}"] = ap
    pd.DataFrame([flat]).to_csv(RESULTS / "baseline_metrics.csv", index=False)
    pd.DataFrame([flat]).to_csv(TABLES / "baseline_metrics.csv", index=False)
    (RESULTS / "baseline_metrics.json").write_text(json.dumps(flat, indent=2, default=str))
    print(json.dumps(flat, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
