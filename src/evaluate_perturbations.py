"""Evaluate the frozen detector on every perturbation condition."""

from __future__ import annotations

import json

import pandas as pd
from PIL import Image

from calculate_metrics import (
    load_yolo_labels,
    mean_average_precision,
    operating_point,
    percentage_change,
    summarize_counts,
)
from config import CLASSES, PERTURBED, RESULTS, TABLES
from evaluate_baseline import class_rows, predict_image
from train_or_load_model import select_device


def main() -> int:
    from ultralytics import YOLO

    weights = RESULTS / "best.pt"
    baseline_path = RESULTS / "baseline_metrics.csv"
    if not weights.exists() or not baseline_path.exists():
        raise SystemExit("Baseline evaluation must be completed first.")
    if not PERTURBED.exists():
        raise SystemExit("No perturbed images. Run generate_perturbations.py first.")

    baseline = pd.read_csv(baseline_path).iloc[0].to_dict()
    device = select_device()
    model = YOLO(str(weights))
    per_image = []
    per_class = []
    condition_rows = []

    for family_dir in sorted(p for p in PERTURBED.iterdir() if p.is_dir()):
        for level_dir in sorted(p for p in family_dir.iterdir() if p.is_dir()):
            images = sorted((level_dir / "images").glob("*.jpg"))
            all_gt = []
            all_det = []
            level_rows = []
            for image_path in images:
                with Image.open(image_path) as image:
                    width, height = image.size
                ground_truth = load_yolo_labels(
                    level_dir / "labels" / f"{image_path.stem}.txt", width, height
                )
                detections, _ = predict_image(model, image_path, device)
                stats = operating_point(ground_truth, detections)
                level_number = int(level_dir.name.replace("level", ""))
                stats.update(
                    {
                        "image_id": image_path.stem,
                        "perturbation": family_dir.name,
                        "level": level_number,
                        "condition": f"{family_dir.name}_level{level_number}",
                    }
                )
                per_image.append(stats)
                level_rows.append(stats)
                per_class.extend(class_rows(image_path.stem, ground_truth, detections))
                per_class[-len(CLASSES) :]  # bound the slice below
                for row in per_class[-len(CLASSES) :]:
                    row["perturbation"] = family_dir.name
                    row["level"] = level_number
                all_gt.append(ground_truth)
                all_det.append(detections)
            summary = summarize_counts(pd.DataFrame(level_rows))
            maps = mean_average_precision(all_gt, all_det)
            summary.update(
                {
                    "perturbation": family_dir.name,
                    "level": int(level_dir.name.replace("level", "")),
                    "map50": maps["map50"],
                    "map50_95": maps["map50_95"],
                    "status": "measured",
                }
            )
            for name, ap in maps["per_class_ap50"].items():
                summary[f"ap50_{name}"] = ap
            for metric in (
                "precision",
                "recall",
                "f1",
                "false_negative_rate",
                "map50",
                "map50_95",
                "mean_iou_tp",
                "mean_confidence_including_misses",
            ):
                summary[f"pct_change_{metric}"] = percentage_change(
                    summary[metric], float(baseline[metric])
                )
            condition_rows.append(summary)
            print(
                f"{family_dir.name} {level_dir.name}: "
                f"recall={summary['recall']:.3f} map50={summary['map50']:.3f} "
                f"fnr={summary['false_negative_rate']:.3f}"
            )

    image_frame = pd.DataFrame(per_image)
    condition_frame = pd.DataFrame(condition_rows)
    class_frame = pd.DataFrame(per_class)
    RESULTS.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    image_frame.to_csv(RESULTS / "perturbation_per_image.csv", index=False)
    condition_frame.to_csv(RESULTS / "perturbation_metrics.csv", index=False)
    condition_frame.to_csv(TABLES / "perturbation_metrics.csv", index=False)
    class_frame.to_csv(RESULTS / "perturbation_per_class_image.csv", index=False)

    class_summary = []
    for (family, level, name), part in class_frame.groupby(["perturbation", "level", "class_name"]):
        row = summarize_counts(part)
        row.update({"perturbation": family, "level": int(level), "class_name": name, "status": "measured"})
        class_summary.append(row)
    pd.DataFrame(class_summary).to_csv(RESULTS / "perturbation_per_class.csv", index=False)
    (RESULTS / "perturbation_status.json").write_text(
        json.dumps({"status": "measured", "n_conditions": len(condition_rows)}, indent=2)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
