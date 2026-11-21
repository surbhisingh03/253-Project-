"""Download the Huang and Wei PCB defect dataset.

The upstream repository is https://github.com/Ironbrotherstyle/PCB-DATASET,
which the dataset paper points readers to via arXiv:1901.08204. This script
does not redistribute the images.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from config import RAW

REPO_URL = "https://github.com/Ironbrotherstyle/PCB-DATASET.git"
DEST = RAW / "PCB-DATASET"


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    if DEST.exists() and any(DEST.rglob("*.jpg")):
        n = sum(1 for _ in DEST.rglob("*.jpg"))
        print(f"Dataset already present at {DEST} ({n} JPEG files).")
        return 0
    if DEST.exists():
        print(f"Removing incomplete checkout at {DEST}")
        subprocess.run(["rm", "-rf", str(DEST)], check=True)
    print(f"Cloning {REPO_URL}")
    subprocess.run(["git", "clone", "--depth", "1", REPO_URL, str(DEST)], check=True)
    n = sum(1 for _ in DEST.rglob("*.jpg"))
    xml = sum(1 for _ in DEST.rglob("*.xml"))
    print(f"Downloaded {n} JPEG files and {xml} XML files.")
    if n == 0:
        print("No images found after clone.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
