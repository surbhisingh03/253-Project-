"""Convert the Huang and Wei VOC annotations into a fixed YOLO split.

Only the aligned, bounding-box-annotated images are used for detection.
Rotated copies, when present, are counted and excluded from training and
testing because their released XML boxes are defined on the aligned images.
The split is stratified by defect category and saved before any perturbation
is generated.
"""

from __future__ import annotations

import json
import random
import shutil
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
import yaml

from config import (
    CLASSES,
    CLASS_TO_ID,
    DATA,
    NAME_ALIASES,
    RAW,
    RESULTS,
    SEED,
    TABLES,
    TEST_RATIO,
    TRAIN_RATIO,
    VAL_RATIO,
    YOLO_DIR,
)


def find_dataset_root() -> Path:
    candidates = [RAW / "PCB-DATASET", RAW]
    for base in candidates:
        if not base.exists():
            continue
        for xml_path in base.rglob("*.xml"):
            return xml_path.parents[2] if xml_path.parent.parent != base else base
    raise FileNotFoundError(
        "No VOC XML files found. Run src/download_dataset.py first."
    )


def locate_roots(dataset_root: Path) -> tuple[Path, Path]:
    anno = None
    images = None
    for path in dataset_root.rglob("*"):
        if path.is_dir() and path.name.lower() == "annotations":
            anno = path
        if path.is_dir() and path.name.lower() == "images":
            images = path
    if anno is None or images is None:
        raise FileNotFoundError(f"Could not find Images and Annotations under {dataset_root}")
    return images, anno


def parse_xml(path: Path) -> tuple[str, int, int, list[dict]]:
    tree = ET.parse(path)
    root = tree.getroot()
    filename = (root.findtext("filename") or path.stem).strip()
    size = root.find("size")
    width = int(float(size.findtext("width"))) if size is not None else 0
    height = int(float(size.findtext("height"))) if size is not None else 0
    objects = []
    for obj in root.findall("object"):
        raw_name = (obj.findtext("name") or "").strip()
        key = NAME_ALIASES.get(raw_name.lower().replace("-", " "), None)
        if key is None:
            key = NAME_ALIASES.get(raw_name.lower().replace(" ", "_"), None)
        box = obj.find("bndbox")
        if box is None:
            continue
        objects.append(
            {
                "raw_name": raw_name,
                "class_name": key,
                "xmin": float(box.findtext("xmin")),
                "ymin": float(box.findtext("ymin")),
                "xmax": float(box.findtext("xmax")),
                "ymax": float(box.findtext("ymax")),
            }
        )
    return filename, width, height, objects


def match_image(images_root: Path, xml_path: Path, filename: str) -> Path | None:
    folder = xml_path.parent.name
    candidates = [
        images_root / folder / filename,
        images_root / folder / xml_path.with_suffix(".jpg").name,
        images_root / folder / f"{xml_path.stem}.jpg",
        images_root / folder / f"{xml_path.stem}.JPG",
        images_root / folder / f"{xml_path.stem}.png",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    stem = xml_path.stem
    for candidate in (images_root / folder).glob(stem + ".*"):
        if candidate.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp"}:
            return candidate
    return None


def yolo_line(cls_id: int, box: dict, width: int, height: int) -> str | None:
    xmin, ymin = box["xmin"], box["ymin"]
    xmax, ymax = box["xmax"], box["ymax"]
    bw = xmax - xmin
    bh = ymax - ymin
    if bw <= 1 or bh <= 1 or width <= 0 or height <= 0:
        return None
    x = ((xmin + xmax) / 2) / width
    y = ((ymin + ymax) / 2) / height
    w = bw / width
    h = bh / height
    x = min(max(x, 0.0), 1.0)
    y = min(max(y, 0.0), 1.0)
    w = min(max(w, 0.0), 1.0)
    h = min(max(h, 0.0), 1.0)
    return f"{cls_id} {x:.6f} {y:.6f} {w:.6f} {h:.6f}"


def stratified_split(records: list[dict]) -> dict[str, str]:
    rng = random.Random(SEED)
    by_class: dict[str, list[str]] = defaultdict(list)
    for rec in records:
        by_class[rec["class_name"]].append(rec["image_id"])
    assignment = {}
    for class_name, ids in by_class.items():
        ids = sorted(set(ids))
        rng.shuffle(ids)
        n = len(ids)
        n_train = int(round(n * TRAIN_RATIO))
        n_val = int(round(n * VAL_RATIO))
        if n_train + n_val >= n:
            n_val = max(1, n - n_train - 1) if n > 2 else 0
        n_train = min(n_train, n - n_val)
        for image_id in ids[:n_train]:
            assignment[image_id] = "train"
        for image_id in ids[n_train : n_train + n_val]:
            assignment[image_id] = "val"
        for image_id in ids[n_train + n_val :]:
            assignment[image_id] = "test"
    return assignment


def main() -> int:
    dataset_root = None
    for base in [RAW / "PCB-DATASET", RAW]:
        if base.exists() and any(base.rglob("*.xml")):
            dataset_root = base
            break
    if dataset_root is None:
        raise SystemExit("Dataset not found. Run download_dataset.py.")

    images_root, anno_root = locate_roots(dataset_root)
    quality_rows = []
    records = []
    unknown_names = Counter()
    missing_images = 0
    out_of_bounds = 0
    zero_area = 0

    for xml_path in sorted(anno_root.rglob("*.xml")):
        filename, width, height, objects = parse_xml(xml_path)
        image_path = match_image(images_root, xml_path, filename)
        if image_path is None:
            missing_images += 1
            quality_rows.append(
                {"xml": str(xml_path), "issue": "missing_image", "detail": filename}
            )
            continue
        class_names = []
        kept = []
        for obj in objects:
            if obj["class_name"] is None:
                unknown_names[obj["raw_name"]] += 1
                quality_rows.append(
                    {
                        "xml": str(xml_path),
                        "issue": "unknown_class",
                        "detail": obj["raw_name"],
                    }
                )
                continue
            bw = obj["xmax"] - obj["xmin"]
            bh = obj["ymax"] - obj["ymin"]
            if bw <= 1 or bh <= 1:
                zero_area += 1
                quality_rows.append(
                    {"xml": str(xml_path), "issue": "non_positive_box", "detail": obj["raw_name"]}
                )
                continue
            if (
                obj["xmin"] < -1
                or obj["ymin"] < -1
                or obj["xmax"] > width + 1
                or obj["ymax"] > height + 1
            ):
                out_of_bounds += 1
                quality_rows.append(
                    {"xml": str(xml_path), "issue": "box_outside_image", "detail": obj["raw_name"]}
                )
            class_names.append(obj["class_name"])
            kept.append(obj)
        if not kept:
            quality_rows.append({"xml": str(xml_path), "issue": "no_valid_objects", "detail": ""})
            continue
        dominant = Counter(class_names).most_common(1)[0][0]
        image_id = f"{dominant}__{image_path.stem}"
        records.append(
            {
                "image_id": image_id,
                "class_name": dominant,
                "image_path": image_path,
                "width": width,
                "height": height,
                "objects": kept,
                "n_objects": len(kept),
                "n_classes_in_image": len(set(class_names)),
            }
        )

    assignment = stratified_split(records)
    if YOLO_DIR.exists():
        shutil.rmtree(YOLO_DIR)
    for split in ("train", "val", "test"):
        (YOLO_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
        (YOLO_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)

    manifest_rows = []
    box_rows = []
    for rec in records:
        split = assignment[rec["image_id"]]
        dest_img = YOLO_DIR / "images" / split / f"{rec['image_id']}.jpg"
        dest_lbl = YOLO_DIR / "labels" / split / f"{rec['image_id']}.txt"
        shutil.copy2(rec["image_path"], dest_img)
        lines = []
        for obj in rec["objects"]:
            cls_id = CLASS_TO_ID[obj["class_name"]]
            line = yolo_line(cls_id, obj, rec["width"], rec["height"])
            if line is None:
                continue
            lines.append(line)
            box_rows.append(
                {
                    "image_id": rec["image_id"],
                    "split": split,
                    "class_name": obj["class_name"],
                    "class_id": cls_id,
                    "xmin": obj["xmin"],
                    "ymin": obj["ymin"],
                    "xmax": obj["xmax"],
                    "ymax": obj["ymax"],
                    "width": rec["width"],
                    "height": rec["height"],
                }
            )
        dest_lbl.write_text("\n".join(lines) + ("\n" if lines else ""))
        manifest_rows.append(
            {
                "image_id": rec["image_id"],
                "split": split,
                "dominant_class": rec["class_name"],
                "n_objects": rec["n_objects"],
                "n_classes_in_image": rec["n_classes_in_image"],
                "width": rec["width"],
                "height": rec["height"],
                "source_image": str(rec["image_path"].relative_to(RAW)),
            }
        )

    manifest = pd.DataFrame(manifest_rows)
    boxes = pd.DataFrame(box_rows)
    RESULTS.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(RESULTS / "split_manifest.csv", index=False)
    boxes.to_csv(RESULTS / "annotations.csv", index=False)
    pd.DataFrame(quality_rows).to_csv(RESULTS / "annotation_quality.csv", index=False)

    summary = (
        boxes.groupby(["split", "class_name"])
        .size()
        .rename("n_boxes")
        .reset_index()
    )
    image_counts = (
        manifest.groupby(["split", "dominant_class"]).size().rename("n_images").reset_index()
    )
    summary.to_csv(TABLES / "dataset_summary_boxes.csv", index=False)
    image_counts.to_csv(TABLES / "dataset_summary_images.csv", index=False)

    yaml_path = YOLO_DIR / "pcb.yaml"
    yaml_path.write_text(
        yaml.safe_dump(
            {
                "path": str(YOLO_DIR.resolve()),
                "train": "images/train",
                "val": "images/val",
                "test": "images/test",
                "names": {i: name for i, name in enumerate(CLASSES)},
            },
            sort_keys=False,
        )
    )

    image_suffixes = {".jpg", ".jpeg", ".png", ".bmp"}
    rotated_images = sum(
        1
        for path in dataset_root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in image_suffixes
        and "rotation" in path.parts
    )

    report = {
        "dataset_root": str(dataset_root),
        "images_root": str(images_root),
        "annotations_root": str(anno_root),
        "n_annotated_images": int(len(manifest)),
        "n_boxes": int(len(boxes)),
        "missing_images": missing_images,
        "unknown_class_counts": dict(unknown_names),
        "out_of_bounds_boxes_flagged": out_of_bounds,
        "zero_area_boxes": zero_area,
        "images_with_mixed_classes": int((manifest["n_classes_in_image"] > 1).sum()),
        "split_counts": manifest["split"].value_counts().to_dict(),
        "class_image_counts": manifest["dominant_class"].value_counts().to_dict(),
        "class_box_counts": boxes["class_name"].value_counts().to_dict(),
        "rotated_image_files_excluded": rotated_images,
        "seed": SEED,
        "ratios": {"train": TRAIN_RATIO, "val": VAL_RATIO, "test": TEST_RATIO},
        "note": (
            "Detection experiments use only images that have VOC bounding boxes. "
            "Rotated images are excluded so that labels are not applied to a "
            "different geometry. Perturbations are created later and only from the test split."
        ),
    }
    (RESULTS / "dataset_report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
