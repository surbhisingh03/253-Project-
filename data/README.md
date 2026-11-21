# Data

The images are not stored in git. Run `python src/download_dataset.py` to clone the public HRIPCB / PCB-DATASET repository.

## What the download contains

The journal paper states that HRIPCB has 1,386 images: 693 aligned defect images and 693 rotated copies, plus 10 template boards. The clone used by this project has that layout.

| Location | Role in this audit |
| --- | --- |
| `images/` | 693 aligned defect images. These are the only images used for training, validation, and testing. |
| `Annotations/` | 693 Pascal VOC XML files. Box counts match the journal table. |
| `rotation/` | 693 rotated images and angle text files. Excluded, because this checkout does not provide transformed boxes. |
| `PCB_USED/` | 10 template images. Not used as detection samples. |

`prepare_dataset.py` writes a YOLO split under `data/yolo/` with seed 253 and a 70/15/15 stratified split. Perturbed test images are written under `data/perturbed/` and are never added to the training split.

## Provenance

- Journal: Huang, Wei, Zhang, and Liu, DOI 10.1049/joe.2019.1183.
- Preprint cited by the course proposal: arXiv:1901.08204.
- Distribution: https://github.com/Ironbrotherstyle/PCB-DATASET

The authors state that the dataset is freely available. The journal article is CC BY 3.0. Do not claim a factory deployment from these files.
