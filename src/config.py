"""Shared paths and audit settings.

All robustness measurements use these constants so the paper, tables, and
figures describe the same experiment.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
YOLO_DIR = DATA / "yolo"
PERTURBED = DATA / "perturbed"
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"
TABLES = ROOT / "tables"
RESEARCH = ROOT / "research"
RUNS = ROOT / "runs"

SEED = 253
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

# Ultralytics YOLOv5u-s. The legacy anchor-based yolov5s.pt checkpoint from
# github.com/ultralytics/yolov5 is not loadable by the current Ultralytics
# library. See docs.ultralytics.com/models/yolov5.
MODEL_WEIGHTS_NAME = "yolov5su.pt"
IMAGE_SIZE = 640
CONF_THRESHOLD = 0.25
NMS_IOU = 0.45
MAP_CONF = 0.001
MATCH_IOU = 0.50
MAX_DET = 100
EPOCHS = int(os.environ.get("EPOCHS", "30"))
BATCH = int(os.environ.get("BATCH", "8"))

CLASSES = [
    "missing_hole",
    "mouse_bite",
    "open_circuit",
    "short",
    "spur",
    "spurious_copper",
]

CLASS_TO_ID = {name: i for i, name in enumerate(CLASSES)}

NAME_ALIASES = {
    "missing_hole": "missing_hole",
    "missing hole": "missing_hole",
    "missinghole": "missing_hole",
    "mouse_bite": "mouse_bite",
    "mouse bite": "mouse_bite",
    "mousebite": "mouse_bite",
    "open_circuit": "open_circuit",
    "open circuit": "open_circuit",
    "opencircuit": "open_circuit",
    "short": "short",
    "short_circuit": "short",
    "short circuit": "short",
    "spur": "spur",
    "spurious_copper": "spurious_copper",
    "spurious copper": "spurious_copper",
    "spuriouscopper": "spurious_copper",
}

DISPLAY_NAMES = {
    "missing_hole": "Missing hole",
    "mouse_bite": "Mouse bite",
    "open_circuit": "Open circuit",
    "short": "Short",
    "spur": "Spur",
    "spurious_copper": "Spurious copper",
}
