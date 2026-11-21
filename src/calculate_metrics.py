"""Detection metrics used by the baseline and perturbation audits.

Operating-point precision, recall, F1, and false-negative rate use a fixed
confidence threshold and a fixed IoU match. Mean average precision is computed
separately from the full confidence sweep, using the 101-point COCO interpolation
at IoU 0.50 and at IoU thresholds 0.50 through 0.95 in steps of 0.05.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from config import CLASSES, CONF_THRESHOLD, MATCH_IOU


def load_yolo_labels(path: Path, width: int, height: int) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    text = path.read_text().strip()
    if not text:
        return rows
    for line in text.splitlines():
        parts = line.split()
        if len(parts) != 5:
            continue
        cls_id = int(parts[0])
        x, y, w, h = map(float, parts[1:])
        xmin = (x - w / 2) * width
        ymin = (y - h / 2) * height
        xmax = (x + w / 2) * width
        ymax = (y + h / 2) * height
        rows.append(
            {
                "class_id": cls_id,
                "class_name": CLASSES[cls_id],
                "xmin": xmin,
                "ymin": ymin,
                "xmax": xmax,
                "ymax": ymax,
            }
        )
    return rows


def iou_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    if len(a) == 0 or len(b) == 0:
        return np.zeros((len(a), len(b)), dtype=float)
    ax1, ay1, ax2, ay2 = a[:, 0:1], a[:, 1:2], a[:, 2:3], a[:, 3:4]
    bx1, by1, bx2, by2 = b[:, 0], b[:, 1], b[:, 2], b[:, 3]
    ix1 = np.maximum(ax1, bx1)
    iy1 = np.maximum(ay1, by1)
    ix2 = np.minimum(ax2, bx2)
    iy2 = np.minimum(ay2, by2)
    inter = np.clip(ix2 - ix1, 0, None) * np.clip(iy2 - iy1, 0, None)
    area_a = np.clip(ax2 - ax1, 0, None) * np.clip(ay2 - ay1, 0, None)
    area_b = np.clip(bx2 - bx1, 0, None) * np.clip(by2 - by1, 0, None)
    union = area_a + area_b - inter
    return np.where(union > 0, inter / union, 0.0)


def boxes_array(rows: list[dict]) -> np.ndarray:
    if not rows:
        return np.zeros((0, 4), dtype=float)
    return np.array([[r["xmin"], r["ymin"], r["xmax"], r["ymax"]] for r in rows], dtype=float)


def match_detections(
    ground_truth: list[dict],
    detections: list[dict],
    iou_threshold: float = MATCH_IOU,
    class_aware: bool = True,
) -> tuple[list[tuple[int, int, float]], set[int], set[int]]:
    """Greedy one-to-one matching, detections assumed sorted by confidence."""
    gt_boxes = boxes_array(ground_truth)
    det_boxes = boxes_array(detections)
    ious = iou_matrix(gt_boxes, det_boxes)
    pairs = []
    used_gt: set[int] = set()
    used_det: set[int] = set()
    order = list(range(len(detections)))
    for det_index in order:
        best_gt = None
        best_iou = iou_threshold
        for gt_index in range(len(ground_truth)):
            if gt_index in used_gt:
                continue
            if class_aware and ground_truth[gt_index]["class_id"] != detections[det_index]["class_id"]:
                continue
            value = ious[gt_index, det_index]
            if value >= best_iou:
                best_iou = value
                best_gt = gt_index
        if best_gt is not None:
            used_gt.add(best_gt)
            used_det.add(det_index)
            pairs.append((best_gt, det_index, float(best_iou)))
    return pairs, used_gt, used_det


def operating_point(ground_truth: list[dict], detections: list[dict]) -> dict:
    kept = [d for d in detections if d["confidence"] >= CONF_THRESHOLD]
    kept = sorted(kept, key=lambda d: d["confidence"], reverse=True)
    pairs, used_gt, used_det = match_detections(ground_truth, kept, MATCH_IOU, class_aware=True)
    tp = len(pairs)
    fp = len(kept) - len(used_det)
    fn = len(ground_truth) - len(used_gt)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    fnr = fn / (tp + fn) if (tp + fn) else 0.0
    mean_iou_tp = float(np.mean([p[2] for p in pairs])) if pairs else float("nan")
    iou_with_misses = ([p[2] for p in pairs] + [0.0] * fn)
    mean_iou_incl = float(np.mean(iou_with_misses)) if iou_with_misses else float("nan")
    conf_tp = [kept[p[1]]["confidence"] for p in pairs]
    conf_incl = conf_tp + [0.0] * fn
    class_changes = 0
    any_pairs, _, _ = match_detections(ground_truth, kept, MATCH_IOU, class_aware=False)
    for gt_index, det_index, _ in any_pairs:
        if ground_truth[gt_index]["class_id"] != kept[det_index]["class_id"]:
            class_changes += 1
    return {
        "n_gt": len(ground_truth),
        "n_det": len(kept),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_negative_rate": fnr,
        "mean_iou_tp": mean_iou_tp,
        "mean_iou_including_misses": mean_iou_incl,
        "mean_confidence_tp": float(np.mean(conf_tp)) if conf_tp else float("nan"),
        "mean_confidence_including_misses": float(np.mean(conf_incl)) if conf_incl else float("nan"),
        "class_inconsistent_matches": class_changes,
        "n_iou_matches_ignoring_class": len(any_pairs),
    }


def _average_precision(recall: np.ndarray, precision: np.ndarray) -> float:
    if len(recall) == 0:
        return 0.0
    recall_levels = np.linspace(0, 1, 101)
    precision_envelope = np.maximum.accumulate(precision[::-1])[::-1]
    interpolated = []
    for level in recall_levels:
        mask = recall >= level
        interpolated.append(float(precision_envelope[mask].max()) if mask.any() else 0.0)
    return float(np.mean(interpolated))


def average_precision_for_class(
    image_gts: list[list[dict]],
    image_dets: list[list[dict]],
    class_id: int,
    iou_threshold: float,
) -> float:
    gt_count = 0
    scored = []
    for gts, dets in zip(image_gts, image_dets):
        gt_cls = [g for g in gts if g["class_id"] == class_id]
        det_cls = sorted(
            [d for d in dets if d["class_id"] == class_id],
            key=lambda d: d["confidence"],
            reverse=True,
        )
        gt_count += len(gt_cls)
        pairs, _, used_det = match_detections(gt_cls, det_cls, iou_threshold, class_aware=True)
        matched = {det_index for _, det_index, _ in pairs}
        for index, det in enumerate(det_cls):
            scored.append((det["confidence"], index in matched))
    if gt_count == 0:
        return float("nan")
    if not scored:
        return 0.0
    scored.sort(key=lambda item: item[0], reverse=True)
    tp = np.cumsum([1 if hit else 0 for _, hit in scored])
    fp = np.cumsum([0 if hit else 1 for _, hit in scored])
    recall = tp / gt_count
    precision = tp / np.maximum(tp + fp, 1)
    return _average_precision(recall, precision)


def mean_average_precision(
    image_gts: list[list[dict]],
    image_dets: list[list[dict]],
) -> dict:
    iou_thresholds = [round(0.50 + 0.05 * i, 2) for i in range(10)]
    per_class_50 = {}
    aps_50 = []
    for class_id, name in enumerate(CLASSES):
        ap = average_precision_for_class(image_gts, image_dets, class_id, 0.50)
        per_class_50[name] = ap
        if not np.isnan(ap):
            aps_50.append(ap)
    map50 = float(np.mean(aps_50)) if aps_50 else float("nan")
    map_range = []
    for threshold in iou_thresholds:
        aps = []
        for class_id in range(len(CLASSES)):
            ap = average_precision_for_class(image_gts, image_dets, class_id, threshold)
            if not np.isnan(ap):
                aps.append(ap)
        if aps:
            map_range.append(float(np.mean(aps)))
    return {
        "map50": map50,
        "map50_95": float(np.mean(map_range)) if map_range else float("nan"),
        "per_class_ap50": per_class_50,
    }


def per_class_operating(image_rows: list[dict]) -> pd.DataFrame:
    """Aggregate TP/FP/FN that were stored per image and per class."""
    return pd.DataFrame(image_rows)


def percentage_change(perturbed: float, baseline: float) -> float:
    if baseline == 0 or np.isnan(baseline) or np.isnan(perturbed):
        return float("nan")
    return (perturbed - baseline) / baseline * 100.0


def summarize_counts(frame: pd.DataFrame) -> dict:
    tp = int(frame["tp"].sum())
    fp = int(frame["fp"].sum())
    fn = int(frame["fn"].sum())
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    fnr = fn / (tp + fn) if (tp + fn) else 0.0
    return {
        "n_images": int(frame["image_id"].nunique()) if "image_id" in frame else int(len(frame)),
        "n_gt": int(frame["n_gt"].sum()),
        "n_det": int(frame["n_det"].sum()),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_negative_rate": fnr,
        "mean_iou_tp": float(frame["mean_iou_tp"].mean(skipna=True)),
        "mean_iou_including_misses": float(frame["mean_iou_including_misses"].mean(skipna=True)),
        "mean_confidence_tp": float(frame["mean_confidence_tp"].mean(skipna=True)),
        "mean_confidence_including_misses": float(
            frame["mean_confidence_including_misses"].mean(skipna=True)
        ),
        "class_inconsistent_matches": int(frame["class_inconsistent_matches"].sum()),
    }
