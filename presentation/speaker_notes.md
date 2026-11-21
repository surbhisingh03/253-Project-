# Speaker notes

Keynote cannot import the notes pages that python-pptx writes, so these notes live in this file.

## Slide 1 — Title

What the slide shows: the audit question, the course, and one real HRIPCB hole.
What I should say: We are not asking whether YOLO can score well on a clean PCB set. We are asking whether that score is something a manufacturer could trust when the picture changes.
Why it matters: Track A is a governance audit. The image is there so the defect stays concrete.
Transition: Start with the decision a missed hole would affect.
Source: Huang, Wei, Zhang, and Liu, The Journal of Engineering, 2020, DOI 10.1049/joe.2019.1183.

## Slide 2 — Manufacturing decision

What the slide shows: one annotated hole and the three-step decision that follows a prediction.
What I should say: The model does not ship a board by itself, but someone will use its miss as a reason to let the board go. That is why a false negative is the failure we care about.
Why it matters: It ties a computer-vision metric to a quality decision.
Transition: That leads to the question we actually tested.
Source: HRIPCB annotation for 01_missing_hole_09.

## Slide 3 — Audit question

What the slide shows: the same hole clean, with noise, and with a gray cover.
What I should say: We froze the weights and changed only the test image. The four failures we counted are a miss, a confidence drop, a class change, and a box that moves off the defect.
Why it matters: This is the research question from the proposal, stated so the rest of the deck can answer it.
Transition: Next, name the exact system, and the limit on what we can claim about it.
Source: results/best.pt predictions on the saved test and perturbation images.

## Slide 4 — System identity

What the slide shows: the exact artifact, data, and operating point.
What I should say: YOLOv5u-s is the checkpoint the current Ultralytics library can train. We fine-tuned it for 30 epochs and then stopped. The yellow line is the limitation the professor needs to hear: this is not a factory model we observed in production.
Why it matters: Track A asks for a known system. We use a public model family and a public dataset, and we do not pretend the fine-tune is already deployed.
Transition: The dataset is the next thing that has to be exact, because the proposal named two different PCB sets.
Source: docs.ultralytics.com/models/yolov5; github.com/ultralytics/yolov5 detect.py; results/environment.json.

## Slide 5 — Dataset

What the slide shows: image counts by class and three real crops.
What I should say: The release has 1,386 images because the rotated half repeats the aligned half. Detection uses the 693 images that have boxes. Our test split is 108 of those, with 477 boxes. Every image has one defect class.
Why it matters: The proposal mixed this set with DeepPCB. DeepPCB is a different 1,500-pair dataset and we did not train on it.
Transition: Now the path from a camera to a decision, including the parts we did not build.
Source: Huang et al. 2020, DOI 10.1049/joe.2019.1183. results/dataset_report.json.

## Slide 6 — Pipeline

What the slide shows: eight stages, colored by what we actually ran.
What I should say: Green is the experiment: resize, the frozen detector, the score, and the 0.25 threshold. Blue is the cell we assume when we talk about governance. Gold is a control we recommend and did not implement. I should not talk as if the log or the quality gate already exists.
Why it matters: The rest of the control plan hangs on this distinction.
Transition: Those stages are also the places an input change, or a file change, can enter.
Source: results/baseline_metrics.csv for the timing. Ultralytics input size 640.

## Slide 7 — Threat model

What the slide shows: six surfaces around the detector, tagged by evidence.
What I should say: The only surface we changed was the image. Camera access is supported by the physical-attack papers, not by a camera trial of our own. Labels, weights, the reviewer, and the log are scenarios. The arrow that matters is image, then miss, then a board that moves forward.
Why it matters: A threat model that marks everything as an attack overclaims the experiment.
Transition: Here is the procedure that produced the measured part.
Source: MITRE ATLAS AML.T0041 for physical environment access. Eykholt et al., arXiv:1807.07769. Lee and Kolter, arXiv:1906.11897.

## Slide 8 — Design

What the slide shows: the sequence and the seven families.
What I should say: We did not retrain between conditions. Each family has three levels. Rotation moves the board, so the boxes move with it. The gray cover is a sensitivity probe on the defect, not an optimized patch.
Why it matters: If I skip the formula, the 73 percent later has no definition.
Transition: Show what four of those conditions look like on one hole.
Source: src/generate_perturbations.py and src/calculate_metrics.py.

## Slide 9 — Example images

What the slide shows: the same hole under four conditions, with the model's own score.
What I should say: On this one hole the clean score is 0.81. Noise drops that score to 0.34 but the hole is still found. A 12-degree rotation still finds it at 0.80. The gray cover, about 30 percent of the box area, removes the detection. I should not say this single hole is the 73 percent dataset drop. That number is the next slide.
Why it matters: The audience can see the failure instead of only hearing a rate.
Transition: First, the clean score those drops are measured against.
Source: panel_results.json from one forward pass of results/best.pt. Per-image counts in results/perturbation_per_image.csv.

## Slide 10 — Baseline

What the slide shows: seven clean-test scores and the miss count.
What I should say: Precision 0.924, recall 0.897, F1 0.911, mAP at 0.5 is 0.921. That looks strong. mAP from 0.5 to 0.95 is 0.455, and the mean overlap of the hits is 0.760. So the boxes clear 0.5 and then fall off. Of 477 defects, 49 were missed. Only 7 overlaps had the wrong class, so the usual clean error is a miss, not a relabel.
Why it matters: A 0.92 mAP would be the end of a benchmark paper. It is the start of this audit.
Transition: Keep that 0.897 recall in mind. The next slide moves it.
Source: results/baseline_metrics.csv and results/per_class_metrics.csv. Lin et al., ECCV 2014, for the COCO AP tradition.

## Slide 11 — Main result

What the slide shows: recall against intensity, with the three numbers I want remembered.
What I should say: Clean recall is 0.897. At noise standard deviation 25, recall falls to 0.241, a 73 percent reduction. Covering about 30 percent of each defect box drops recall to 0.036. Rotation declines more slowly, to 0.672 at 12 degrees. Blur, JPEG, and brightness stay near the clean line. A 15-pixel blur on a 3,000-pixel image is mild after the 640 resize, so I should not say blur is harmless in general.
Why it matters: This is the evidence slide. Everything after it interprets these curves.
Transition: The average hides which defect classes fail.
Source: results/perturbation_metrics.csv. Percentage change formula on the design slide.

## Slide 12 — Per class

What the slide shows: recall by class for the clean test, moderate noise, the middle cover, and a 12-degree rotation.
What I should say: Missing holes and shorts start near 0.99. Under noise, spurs go to zero and spurious copper goes to 0.01, while missing-hole recall is still 0.87. The cover is harsher: five classes go to zero, and spur is the only class with recall left, 0.21. I should not call every class equally fragile. The dominant error is still a miss. Wrong class was uncommon on the clean test.
Why it matters: A single recall number would hide that thin copper defects fail first.
Transition: Turn that miss into the operational chain, and keep the chain labeled as measured or possible.
Source: results/perturbation_per_class.csv and results/baseline_metrics.csv.

## Slide 13 — Cause and effect

What the slide shows: a five-step chain, with the last two steps marked possible rather than observed.
What I should say: We measured the left side: the image changed, scores fell or boxes disappeared, and the false-negative rate rose. We did not watch a factory accept a bad board. Rework and a customer return are what that miss could cost if the cell auto-accepts. I should say "could," not "did."
Why it matters: This is the line between an experiment and a governance claim.
Transition: ATLAS is how we name the techniques, and NIST is how we would manage them.
Source: results/perturbation_metrics.csv. NIST AI RMF, NIST AI 100-1, DOI 10.6028/NIST.AI.100-1.

## Slide 14 — ATLAS and controls

What the slide shows: six ATLAS names with an evidence label, and five controls.
What I should say: Craft Adversarial Data, including manual modification, is the name for the edits we actually ran. Physical Environment Access is in the literature; we did not touch a real camera. Evade AI Model, eroding integrity, swapping weights, and poisoning labels are scenarios. The controls on the right do not erase those risks. They make a miss harder to auto-accept. NIST's frame for that plan is Govern, Map, Measure, Manage.
Why it matters: The professor asked for evidence-first mapping, not a list of every ATLAS ID.
Transition: Close with the release rule that follows from the curves.
Source: github.com/mitre-atlas/atlas-data ATLAS-2026.10.yaml. Pages are atlas.mitre.org/techniques/ plus the ID. NIST AI 100-1.

## Slide 15 — Release decision

What the slide shows: a conditional release, six gates, three conclusions, and the limits.
What I should say: I would not turn automatic accept on for this checkpoint. Clean recall of 0.897 coexists with a 73 percent recall drop under moderate noise and a near-total miss when the defect is covered. The gates are how an organization would use the model anyway: reject bad frames, hold weak scores, watch each class, log the file that made the call, and retest when the camera changes. The limits box is part of the answer. These are research images, the edits were digital, and we did not see this file run in a factory.
Why it matters: It is the decision the audit was for.
Transition: Stop. Take questions on the noise curve, the cover, or the factory limitation.
Source: results/perturbation_per_class.csv for the per-class noise bar. NIST AI RMF Playbook, nist.gov.
