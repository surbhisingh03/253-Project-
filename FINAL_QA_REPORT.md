# Final quality-control report

Date of this check: 21 November 2026. The paper and slides describe the run that is already on disk. No metric in the paper was typed in ahead of the CSV that produced it.

## Proposal coverage

The proposal asks how robust an established PCB defect detector is under controlled input changes, and what operational and security risks those changes create. The failures named in the proposal are a missed defect, a changed class, a lower confidence, and a moved box. The paper reports all four. Class changes are uncommon (7 of 434 class-agnostic overlaps on the clean test). The large effects are misses.

The proposal names both DeepPCB and a 1,386-image Huang and Wei set. Those are different datasets. The audit uses HRIPCB and says so in Section IV. DeepPCB (1,500 pairs, IoU 0.33, 98.6 percent mAP) is related work only.

Track A items that are in the package: a named public model family, a frozen evaluation, a threat model, MITRE ATLAS identifiers checked against content 2026.10, a NIST AI RMF Govern / Map / Measure / Manage plan, an assurance matrix, and a statement that controls do not remove residual risk.

## Experiments

Completed, and used as findings:

1. Dataset parse, quality check, and stratified split.
2. Fine-tune of YOLOv5u-s for 30 epochs, then a frozen test evaluation.
3. Nine perturbation families at three intensities on the 108 test images only.
4. Localized gray occlusion on annotated boxes, labeled as a sensitivity test.
5. Risk register, control-coverage table, assurance matrix, and figures 1–12.

Not run, and not reported as results:

- Detection on the rotated HRIPCB half. The checkout does not transform the boxes.
- An optimized adversarial patch, a physical camera trial, or any edit of a system this project does not own.
- Weight replacement, label poisoning, and a networked inference API.
- A pycocotools cross-check of the 101-point mAP implementation. The unit check is a perfect detection (AP 1) and a total miss (AP 0).

No planned stage failed after the scripts were corrected. The rotated-image counter originally double-counted folders; `prepare_dataset.py` now counts 693 rotated files, and the split was rebuilt before training.

## Numbers and their sources

Clean test, `results/baseline_metrics.csv`: 108 images, 477 boxes, 428 true positives, 35 false positives, 49 false negatives, precision 0.924, recall 0.897, F1 0.911, FNR 0.103, mAP@0.5 0.921, mAP@0.5:0.95 0.455, mean IoU of true positives 0.760, mean confidence with misses as zero 0.620, 38.9 ms per image after warmup.

Recall by family is Table II of the paper and `results/perturbation_metrics.csv`. Level-2 percentage changes use (perturbed − baseline) / baseline × 100: noise −73.1 percent, occlusion −96.0 percent, 12-degree rotation −25.1 percent.

Published scores that are not this audit: DeepPCB 98.6 percent mAP, Niu et al. 99.1 percent mAP, Xiao et al. 98.3 percent mAP, and Eykholt et al. indoor miss rates. Each is cited to its paper.

Risk scores for R1–R5 use the level-2 recall drop. R6–R10 are marked `scenario_assessment` in `results/risk_register.csv`. Impact is a judgment. No chart is labeled as an illustrative example; `figures/figure_status.csv` marks figures 1–10 and 12 as measured and figure 11 as source-mapped from the ATLAS table.

## Citations

Every `\cite` key in `main.tex` is in `references.bib`. The compiled PDF has references [1]–[16] and no unresolved citation marks. ATLAS names and identifiers were taken from the 2026.10 YAML at https://github.com/mitre-atlas/atlas-data/blob/main/dist/v6/ATLAS-2026.10.yaml. Tactic lists are from the 5.6.0 matrix because the 2026.10 technique objects do not repeat them. The paper says that. AML.T0076 is unused because the 2026.10 text uses it for scanner-evasion during deserialization, not for swapping a checkpoint. NIST AI 100-1 is Tabassi, January 2023, DOI 10.6028/NIST.AI.100-1. The Playbook URL is the NIST page cited in the bibliography.

## Paper layout

`ieee_paper/final_paper.pdf` is 9 letter pages, compiled with Tectonic from `main.tex`. All nine pages were rendered and read.

Checked and acceptable:

- Two columns stay inside the page.
- Figure titles inside the PNGs no longer carry a second figure number. Captions are Fig. 1 through Fig. 9.
- The comparison crop, recall chart, false-negative chart, mAP chart, class heatmap, and risk grid are readable.
- Tables I–IV wrap. Table III is wide and floats to the page with the conclusion. The text points to it before it appears.
- References are continuous and are not interrupted by a figure.

Remaining layout notes:

- Table IV has a TeX overfull box of 1.9 pt. The words in that table are present; the overflow is a fraction of a millimeter.
- Fig. 9 is one column wide, so the control names are small. The full-size file is `figures/fig12_control_coverage.png`. Putting that figure across both columns pushed it into the bibliography, so it was returned to one column.
- Matplotlib warned that DejaVu Sans has no semibold face and used weight 700. The titles are still bold.

## Slides

`presentation/final_presentation.pptx` has 17 slides: the 16-slide narrative plus the required references slide. Speaker notes are in the file and in `presentation/speaker_notes.md`.

A geometry pass confirmed that no shape extends past the 13.333 by 7.5 inch slide. Body bullets are 26–28 pt. The ATLAS table is 18 pt and the references slide is 20 pt so the rows fit. Charts on slides 11 and 12 are native PowerPoint charts, so the values can be edited. PCB crops are the HRIPCB test image and the three-panel comparison.

Keynote would not accept Apple Events (`-1743`), so the deck was not exported to a PDF for a pixel-by-pixel pass. Opening Keynote raised its document chooser; that chooser was cancelled and no other file was opened. Coordinate checks and a reading of every slide’s text are the inspection that was completed.

## Ethical boundary

Perturbations are offline copies of a public dataset. The gray rectangle covers an annotated defect in order to measure dependence on local appearance. The repository does not contain an optimized patch, a physical placement procedure, or instructions for hiding defects on a line the authors do not operate.
