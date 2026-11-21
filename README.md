# Robustness and Security Audit of an AI-Based PCB Defect Detection System

CMPE 253, San Jose State University, Fall 2026. Track A: governance audit and threat mapping.

Authors: Nirupam Narayana Maladi and Surbhi Singh.

The audited detector is Ultralytics YOLOv5u-s (`yolov5su.pt`), fine-tuned for 30 epochs on the aligned half of the public HRIPCB dataset and then frozen. It is a reproducible research prototype. The paper does not claim that this checkpoint runs in a factory.

## What is already measured

The numbers in `ieee_paper/final_paper.pdf`, the slides, and `results/` come from one completed run:

- 693 aligned images, 2,953 boxes, split 483 / 102 / 108 with seed 253
- Clean test: precision 0.924, recall 0.897, F1 0.911, FNR 0.103, mAP@0.5 0.921, mAP@0.5:0.95 0.455, on 477 boxes
- Nine perturbation families at three intensities, evaluated with the same checkpoint

`train_or_load_model.py` retrains only when `runs/pcb_yolov5su/weights/best.pt` is absent. Leave that file in place to reproduce the reported metrics.

## Environment

The recorded run used Python 3.14.5, PyTorch 2.15.0 (Metal), Ultralytics 8.4.216, OpenCV 5.1.0, and NumPy 2.5.5 on an Apple M4. CUDA was not available. See `results/environment.json`.

```bash
cd "/Users/surbhisingh/253 final proj"
python3 -m venv .venv
.venv/bin/pip install -r project/requirements.txt
```

The IEEE PDF was built with the Tectonic binary at `project/.tools/tectonic`. A system `pdflatex` is not required.

## Reproduce

```bash
cd "/Users/surbhisingh/253 final proj/project"
../.venv/bin/python src/download_dataset.py
../.venv/bin/python src/prepare_dataset.py
../.venv/bin/python src/train_or_load_model.py
../.venv/bin/python src/evaluate_baseline.py
../.venv/bin/python src/generate_perturbations.py
../.venv/bin/python src/evaluate_perturbations.py
../.venv/bin/python src/generate_risk_tables.py
../.venv/bin/python src/generate_figures.py
../.venv/bin/python src/build_presentation.py
cd ieee_paper && ../.tools/tectonic main.tex && cp -f main.pdf final_paper.pdf
```

`download_dataset.py` clones https://github.com/Ironbrotherstyle/PCB-DATASET into `data/raw/`. Images, YOLO labels, perturbed copies, and `*.pt` weights are gitignored.

## Dataset note

HRIPCB and DeepPCB are different collections. This audit uses the aligned HRIPCB half: 693 images and 2,953 boxes, matching Table 1 of Huang, Wei, Zhang, and Liu, *The Journal of Engineering*, 2020, DOI 10.1049/joe.2019.1183. The rotated half is excluded because this checkout has angle files rather than transformed boxes. Details are in `data/README.md` and `research/literature_review.md`.

## Layout

| Path | Contents |
| --- | --- |
| `ieee_paper/final_paper.pdf` | IEEE conference paper |
| `ieee_paper/main.tex` | Editable source |
| `ieee_paper/references.bib` | Bibliography |
| `presentation/final_presentation.pptx` | 16 narrative slides plus a references slide |
| `presentation/speaker_notes.md` | Notes copied from the deck |
| `src/` | Dataset, training, evaluation, figures, risk tables, slides |
| `results/` | Measured CSVs |
| `figures/` | Charts and example crops |
| `tables/` | Tables used by the paper and slides |
| `research/` | Source log, literature note, ATLAS mapping |
| `FINAL_QA_REPORT.md` | Quality-control record |
