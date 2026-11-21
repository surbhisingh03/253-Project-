# Literature review and source notes

This note records what was verified before the paper was written. It separates the course proposal, the published dataset papers, and the measurements made in this repository.

## Research question carried forward from the proposal

The proposal asks how robust an established PCB defect detector is against controlled input perturbations, and which operational and security risks appear when those perturbations change model performance. The specific failure modes are a missed defect, a changed class, a lower confidence, and a moved box. The governance task is to turn those observations into a threat mapping and a control plan.

The proposal's expected findings were written before the experiment. They are not treated as results. The paper reports only the measurements produced by `src/`.

## Dataset discrepancy

The proposal uses two dataset descriptions.

- Background citation [1] is DeepPCB from Tang, He, Huang, and Yang, arXiv:1902.06197. That dataset has 1,500 image pairs. Each pair is a 640 by 640 template and a tested image. The six classes are open, short, mousebite, spur, pin-hole, and spurious copper. The paper reports 98.6 percent mAP, and it counts a detection as correct when the intersection over union is greater than 0.33. DeepPCB is related work. It is not the dataset audited here.
- Methods citation [7] is Huang and Wei, arXiv:1901.08204. The later journal version is Huang, Wei, Zhang, and Liu, "HRIPCB," *The Journal of Engineering*, vol. 2020, iss. 13, pp. 303-309, 2020, DOI 10.1049/joe.2019.1183. The journal states that HRIPCB contains 1,386 synthesized images. Half are aligned defect images and half are rotated copies. Table 1 lists only the aligned half, because the authors say the rotated half has the same counts: missing hole 115 images (497 defects), mouse bite 115 (492), open circuit 116 (482), short 116 (491), spur 115 (488), and spurious copper 116 (503).

The GitHub checkout at `Ironbrotherstyle/PCB-DATASET` was counted by `src/prepare_dataset.py`. It contains 693 XML annotation files, 693 aligned JPEG images, 693 rotated JPEG images, and 10 template images in `PCB_USED`. The aligned image and box counts match Table 1 exactly: 693 images and 2,953 boxes. The rotated images have angle text files and do not have a separate bounding-box XML in this checkout, so they are excluded from detection training and testing. Applying the aligned boxes to a rotated image would be a label error.

The journal says each image has three to five defects. The parsed aligned annotations are mostly in that range, but the file count is not identical to the sentence: 1 image has 1 box, 16 have 2, 232 have 3, 14 have 4, 412 have 5, and 18 have 6. The paper reports the counted distribution.

The arXiv preprint text describes the largest board as 20 mm by 120 mm. The journal text says the largest board is 120 mm by 120 mm and the smallest is 53 mm by 48 mm. This project uses the journal statement for physical board size and uses the pixel sizes measured from the XML files for the images that were actually loaded. Those pixel widths range from 2,240 to 3,056 and the heights range from 1,586 to 2,530.

The journal article is published under the Creative Commons Attribution License. The authors say the dataset is freely available. The GitHub README does not add a separate SPDX license. The images are kept out of git and are downloaded by the script.

HRIPCB is a public research dataset built to resemble an automated optical inspection cell. It is not, by itself, evidence that the fine-tuned model in this project is installed in a factory. The acquisition description in the journal is a laboratory setup: a 16-megapixel industrial camera, a 6-12 mm lens, and two diffuse ring lights. Defects were added in Photoshop.

## What "the audited system" is

Published PCB papers show that YOLOv5-family detectors are a realistic inspection architecture. Niu, Li, Chen, and Qian report 99.1 percent mAP for an improved YOLOv5 on a public defect dataset. Xiao, Hou, and Zhou report 98.3 percent mAP for CDI-YOLO after cropping the Peking University images into 10,668 smaller images. Those numbers belong to those papers. They are not baseline numbers for this audit.

The implementation loaded here is the Ultralytics YOLOv5u small checkpoint `yolov5su.pt`, documented at https://docs.ultralytics.com/models/yolov5. Ultralytics states that weights trained in the original `ultralytics/yolov5` repository cannot be loaded by the current Ultralytics library, and that `yolov5su.pt` is the supported small model. The checkpoint is COCO-pretrained and was fine-tuned in this project. The fine-tuned file is a reproducible research prototype. It is not described as a production weight file from a manufacturer.

The original YOLOv5 `detect.py` defaults, used as the operating point, are confidence 0.25, image size 640, and NMS IoU 0.45.

## Adversarial literature, and what this project does not do

Eykholt et al. showed that a physical poster or stickers can make a YOLOv2 detector miss a Stop sign in a large fraction of video frames. Lee and Kolter showed that an optimized patch can suppress YOLOv3 detections even for objects the patch does not cover. Brown et al. showed a targeted patch against classifiers. Those papers support the threat scenario that a localized physical change can affect a detector.

This repository does not implement those optimization procedures. The security-relevant laboratory condition is a gray rectangle covering a stated fraction of each annotated defect box. It measures whether hiding defect evidence changes the frozen detector. It is labeled as a controlled occlusion-sensitivity test.

## Governance sources

NIST AI RMF 1.0 (NIST AI 100-1, January 2023, DOI 10.6028/NIST.AI.100-1), written by Elham Tabassi, organizes risk management into Govern, Map, Measure, and Manage. The NIST AI RMF Playbook supplies suggested actions for those functions. The audit uses the four functions as the structure of the governance section. It does not claim that completing the section certifies the system.

MITRE ATLAS content version 2026.10, modified 28 October 2026, is the source for technique names and identifiers. The mapping table in `research/atlas_mapping.csv` records whether each row is a laboratory observation, a literature-supported scenario, or an untested scenario. AML.T0076, "Corrupt AI Model," is not used. In the 2026.10 text that technique means corrupting a model file so a scanner fails during deserialization. Weight substitution is discussed under AML.T0018, "Manipulate AI Model," and AML.T0018.000, "Poison AI Model."

## Metrics

Precision, recall, F1, and false-negative rate are computed at confidence 0.25 with a one-to-one IoU match of at least 0.50. False-negative rate is FN / (TP + FN). Mean average precision uses 101-point interpolated average precision. mAP@0.5:0.95 averages that quantity at IoU thresholds from 0.50 to 0.95 in steps of 0.05. Percentage change is (perturbed - baseline) / baseline × 100, as stated in the proposal. A negative percentage change in recall is a degradation. A positive percentage change in false-negative rate is also a degradation.
