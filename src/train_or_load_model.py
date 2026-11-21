"""Fine-tune the public Ultralytics YOLOv5u-s checkpoint and freeze it.

The COCO-pretrained checkpoint is the documented Ultralytics YOLOv5u small
model (yolov5su.pt). Fine-tuning uses only the training and validation splits.
Test images, including every later perturbation, are not used for training.
"""

from __future__ import annotations

import json
import platform
import shutil
from pathlib import Path

from config import (
    BATCH,
    CLASSES,
    CONF_THRESHOLD,
    EPOCHS,
    IMAGE_SIZE,
    MODEL_WEIGHTS_NAME,
    NMS_IOU,
    RESULTS,
    RUNS,
    YOLO_DIR,
)


def select_device() -> str:
    import torch

    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda:0"
    return "cpu"


def environment_record(device: str) -> dict:
    import cv2
    import numpy
    import torch
    import ultralytics

    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "torch": torch.__version__,
        "torch_mps": bool(torch.backends.mps.is_available()),
        "torch_cuda": bool(torch.cuda.is_available()),
        "ultralytics": ultralytics.__version__,
        "opencv": cv2.__version__,
        "numpy": numpy.__version__,
        "device": device,
        "model_weights_name": MODEL_WEIGHTS_NAME,
        "image_size": IMAGE_SIZE,
        "conf_threshold": CONF_THRESHOLD,
        "nms_iou": NMS_IOU,
        "epochs_requested": EPOCHS,
        "batch": BATCH,
        "classes": CLASSES,
        "pretrained": True,
        "training_data": "Huang and Wei aligned annotated images, train split only",
    }


def main() -> int:
    from ultralytics import YOLO

    RESULTS.mkdir(parents=True, exist_ok=True)
    data_yaml = YOLO_DIR / "pcb.yaml"
    if not data_yaml.exists():
        raise SystemExit("Missing data/yolo/pcb.yaml. Run prepare_dataset.py first.")

    device = select_device()
    record = environment_record(device)
    best_link = RESULTS / "best.pt"
    run_dir = RUNS / "pcb_yolov5su"
    weights = run_dir / "weights" / "best.pt"

    if weights.exists():
        print(f"Using existing fine-tuned weights at {weights}")
    else:
        model = YOLO(MODEL_WEIGHTS_NAME)
        batch = BATCH if device != "cpu" else min(BATCH, 4)
        model.train(
            data=str(data_yaml),
            epochs=EPOCHS,
            imgsz=IMAGE_SIZE,
            batch=batch,
            device=device,
            workers=2 if device != "cpu" else 0,
            seed=253,
            project=str(RUNS),
            name="pcb_yolov5su",
            exist_ok=True,
            pretrained=True,
            patience=10,
            plots=True,
            val=True,
            verbose=True,
        )
        produced = Path(model.trainer.best) if getattr(model, "trainer", None) else weights
        if not produced.exists():
            produced = weights
        if not produced.exists():
            raise SystemExit("Training finished without a best.pt checkpoint.")
        weights = produced

    if best_link.exists() or best_link.is_symlink():
        best_link.unlink()
    shutil.copy2(weights, best_link)
    record["checkpoint"] = str(best_link.resolve())
    record["source_checkpoint"] = str(weights.resolve())
    record["status"] = "trained_or_loaded"
    (RESULTS / "environment.json").write_text(json.dumps(record, indent=2))
    print(json.dumps(record, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
