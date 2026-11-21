"""Fifteen-slide evidence deck for the CMPE 253 Track A audit.

Speaker notes are written to presentation/speaker_notes.md. They are not stored
inside the PPTX: Keynote rejects the notes-slide package that python-pptx writes.
"""

from __future__ import annotations

import json

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.oxml import parse_xml
from pptx.util import Emu, Inches, Pt

from config import FIGURES, ROOT

NAVY = RGBColor(0x0B, 0x1F, 0x3A)
GREEN = RGBColor(0x1F, 0x8A, 0x4C)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
INK = RGBColor(0x12, 0x20, 0x2B)
MUTED = RGBColor(0x4E, 0x5D, 0x6B)
RED = RGBColor(0xB4, 0x23, 0x18)
BLUE = RGBColor(0x1D, 0x4E, 0x89)
GOLD = RGBColor(0x8A, 0x5A, 0x12)
PALE = RGBColor(0xF3, 0xF6, 0xF4)
PALE_RED = RGBColor(0xF8, 0xE8, 0xE6)
PALE_BLUE = RGBColor(0xE7, 0xEE, 0xF6)
PALE_GOLD = RGBColor(0xF8, 0xF1, 0xE3)

W = Inches(13.333)
H = Inches(7.5)
SLIDES = FIGURES / "slides"
NOTES: list[tuple[str, str]] = []


def set_run(paragraph, text, size, bold=False, color=INK, align=PP_ALIGN.LEFT, font="Calibri"):
    paragraph.clear()
    paragraph.alignment = align
    lines = text.split("\n")
    for index, line in enumerate(lines):
        run = paragraph.add_run()
        run.text = line
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = color
        run.font.name = font
        if index < len(lines) - 1:
            paragraph._p.append(parse_xml(
                '<a:br xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"/>'
            ))


def add_text(slide, text, l, t, w, h, size=20, bold=False, color=INK, align=PP_ALIGN.LEFT):
    box = slide.shapes.add_textbox(l, t, w, h)
    frame = box.text_frame
    frame.word_wrap = True
    set_run(frame.paragraphs[0], text, size, bold, color, align)
    return box


def add_rect(slide, l, t, w, h, fill, line=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h)
    shape.adjustments[0] = 0.08
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    if line is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line
        shape.line.width = Pt(1.25)
    return shape


def add_picture(slide, path, left, top, max_w, max_h):
    from PIL import Image

    with Image.open(path) as image:
        width, height = image.size
    scale = min(max_w / width, max_h / height)
    return slide.shapes.add_picture(str(path), left, top, width=Emu(int(width * scale)), height=Emu(int(height * scale)))


def footer(slide, text, dark=False):
    add_text(slide, text, Inches(0.4), Inches(7.12), Inches(12.5), Inches(0.28), 12, False, RGBColor(0xC5, 0xD0, 0xC8) if dark else MUTED)


def blank(prs, dark=False):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = NAVY if dark else WHITE
    return slide


def drop_theme_styles(prs: Presentation) -> None:
    tag = "{http://schemas.openxmlformats.org/presentationml/2006/main}style"
    for slide in prs.slides:
        for style in list(slide.shapes._spTree.iter(tag)):
            parent = style.getparent()
            if parent is not None:
                parent.remove(style)


def remember(title, note):
    NOTES.append((title, note))


def main():
    panels = json.loads((SLIDES / "panel_results.json").read_text())
    by_key = {row["key"]: row for row in panels}
    prs = Presentation()
    prs.slide_width = W
    prs.slide_height = H
    prs.core_properties.title = "Can a PCB Defect Detector Be Trusted Outside the Clean Benchmark?"
    prs.core_properties.author = "Nirupam Narayana Maladi and Surbhi Singh"
    prs.core_properties.subject = "CMPE 253 Track A"

    # 1
    slide = blank(prs, dark=True)
    add_text(slide, "CMPE 253  ·  Track A  ·  Fall 2026", Inches(0.55), Inches(0.42), Inches(7.4), Inches(0.4), 18, False, GREEN)
    add_text(
        slide,
        "Can a PCB Defect Detector Be Trusted\nOutside the Clean Benchmark?",
        Inches(0.55), Inches(1.15), Inches(7.6), Inches(2.3), 36, True, WHITE,
    )
    add_text(
        slide,
        "Robustness and Security Audit of a\nYOLO-Based PCB Inspection System",
        Inches(0.55), Inches(3.6), Inches(7.4), Inches(1.2), 22, False, RGBColor(0xD5, 0xE4, 0xDA),
    )
    add_text(
        slide,
        "Nirupam Narayana Maladi and Surbhi Singh\nSan Jose State University",
        Inches(0.55), Inches(5.5), Inches(7.2), Inches(1.0), 20, False, WHITE,
    )
    add_picture(slide, SLIDES / "title_crop.jpg", Inches(8.45), Inches(1.35), Inches(4.4), Inches(4.7))
    footer(slide, "HRIPCB test image, missing-hole class. Huang, Wei, Zhang, and Liu, 2020.", dark=True)
    remember("Title", """What the slide shows: the audit question, the course, and one real HRIPCB hole.
What I should say: We are not asking whether YOLO can score well on a clean PCB set. We are asking whether that score is something a manufacturer could trust when the picture changes.
Why it matters: Track A is a governance audit. The image is there so the defect stays concrete.
Transition: Start with the decision a missed hole would affect.
Source: Huang, Wei, Zhang, and Liu, The Journal of Engineering, 2020, DOI 10.1049/joe.2019.1183.""")

    # 2
    slide = blank(prs)
    add_text(slide, "A missed defect is a release decision", Inches(0.45), Inches(0.28), Inches(12), Inches(0.55), 32, True, NAVY)
    add_picture(slide, SLIDES / "decision_crop.jpg", Inches(0.4), Inches(1.15), Inches(6.6), Inches(5.5))
    steps = [("PCB image", "What the camera captured"), ("Model output", "Class, box, confidence"), ("Accept or hold", "The board moves or it does not")]
    top = 1.35
    for title, body in steps:
        add_rect(slide, Inches(7.3), Inches(top), Inches(5.5), Inches(1.15), PALE, GREEN)
        add_text(slide, title, Inches(7.5), Inches(top + 0.12), Inches(5.1), Inches(0.45), 22, True, NAVY)
        add_text(slide, body, Inches(7.5), Inches(top + 0.55), Inches(5.1), Inches(0.45), 18, False, INK)
        top += 1.35
    add_text(slide, "A false negative can allow a defective board to move forward.", Inches(7.3), Inches(5.5), Inches(5.5), Inches(1.2), 22, True, RED)
    footer(slide, "Highlighted box is a ground-truth missing hole on test image 01_missing_hole_09. Not a factory incident.")
    remember("Manufacturing decision", """What the slide shows: one annotated hole and the three-step decision that follows a prediction.
What I should say: The model does not ship a board by itself, but someone will use its miss as a reason to let the board go. That is why a false negative is the failure we care about.
Why it matters: It ties a computer-vision metric to a quality decision.
Transition: That leads to the question we actually tested.
Source: HRIPCB annotation for 01_missing_hole_09.""")

    # 3
    slide = blank(prs)
    add_text(slide, "How does a fixed detector behave when the image changes?", Inches(0.4), Inches(0.22), Inches(12.5), Inches(0.7), 28, True, NAVY)
    trio = [("none", "Original"), ("noise", "Noise, σ = 25"), ("occlusion", "Gray cover on the hole")]
    left = 0.4
    for key, label in trio:
        add_picture(slide, SLIDES / f"panel_{key}.jpg", Inches(left), Inches(1.15), Inches(4.05), Inches(3.7))
        add_text(slide, label, Inches(left), Inches(4.95), Inches(4.0), Inches(0.4), 18, True, NAVY, PP_ALIGN.CENTER)
        left += 4.25
    add_text(slide, "A failure is a missed defect, a lower confidence, a wrong class, or a box that no longer sits on the defect.", Inches(0.5), Inches(5.55), Inches(12.3), Inches(0.9), 20, False, INK)
    footer(slide, "Same missing hole. Predictions from the frozen YOLOv5u-s checkpoint, confidence threshold 0.25.")
    remember("Audit question", """What the slide shows: the same hole clean, with noise, and with a gray cover.
What I should say: We froze the weights and changed only the test image. The four failures we counted are a miss, a confidence drop, a class change, and a box that moves off the defect.
Why it matters: This is the research question from the proposal, stated so the rest of the deck can answer it.
Transition: Next, name the exact system, and the limit on what we can claim about it.
Source: results/best.pt predictions on the saved test and perturbation images.""")

    # 4
    slide = blank(prs, dark=True)
    add_text(slide, "What was audited", Inches(0.5), Inches(0.28), Inches(12), Inches(0.55), 32, True, WHITE)
    rows = [
        ("Public artifact", "Ultralytics YOLOv5u-s, yolov5su.pt"),
        ("Data", "HRIPCB aligned images, six defect classes"),
        ("Training", "30 epochs from COCO-pretrained weights"),
        ("Then frozen", "No perturbed image entered training"),
        ("Input", "Letterbox to 640 pixels"),
        ("Threshold", "Confidence 0.25, NMS IoU 0.45"),
        ("Evaluation", "Offline, original test images only"),
    ]
    top = 1.05
    for label, value in rows:
        add_rect(slide, Inches(0.5), Inches(top), Inches(3.1), Inches(0.68), GREEN)
        add_text(slide, label, Inches(0.65), Inches(top + 0.12), Inches(2.8), Inches(0.45), 18, True, WHITE)
        add_text(slide, value, Inches(3.8), Inches(top + 0.12), Inches(8.8), Inches(0.45), 20, False, WHITE)
        top += 0.74
    add_text(slide, "This project audits a reproducible research system. It does not claim that this exact model is deployed in a factory.", Inches(0.5), Inches(6.4), Inches(12.3), Inches(0.65), 18, True, RGBColor(0xF2, 0xD4, 0x8A))
    footer(slide, "Ultralytics YOLOv5 docs. YOLOv5 detect.py defaults. Trainer validation mAP is not the audit metric.", dark=True)
    remember("System identity", """What the slide shows: the exact artifact, data, and operating point.
What I should say: YOLOv5u-s is the checkpoint the current Ultralytics library can train. We fine-tuned it for 30 epochs and then stopped. The yellow line is the limitation the professor needs to hear: this is not a factory model we observed in production.
Why it matters: Track A asks for a known system. We use a public model family and a public dataset, and we do not pretend the fine-tune is already deployed.
Transition: The dataset is the next thing that has to be exact, because the proposal named two different PCB sets.
Source: docs.ultralytics.com/models/yolov5; github.com/ultralytics/yolov5 detect.py; results/environment.json.""")

    # 5
    slide = blank(prs)
    add_text(slide, "HRIPCB: six classes, one class per image", Inches(0.4), Inches(0.22), Inches(12), Inches(0.5), 30, True, NAVY)
    add_picture(slide, SLIDES / "class_distribution.png", Inches(0.15), Inches(0.85), Inches(8.0), Inches(5.9))
    crops = [("class_missing_hole.jpg", "Missing hole"), ("class_spur.jpg", "Spur"), ("class_spurious_copper.jpg", "Spurious copper")]
    top = 1.05
    for name, label in crops:
        add_picture(slide, SLIDES / name, Inches(8.3), Inches(top), Inches(2.15), Inches(1.45))
        add_text(slide, label, Inches(10.55), Inches(top + 0.4), Inches(2.5), Inches(0.7), 16, True, NAVY)
        top += 1.55
    add_text(slide, "693 detection images\n2,953 boxes\n108 test images, 477 boxes\nAlso: open, short, mouse bite", Inches(8.3), Inches(5.7), Inches(4.6), Inches(1.3), 16, False, INK)
    footer(slide, "Aligned half only. Journal Table 1. Rotated copies excluded: this checkout has angles, not transformed boxes.")
    remember("Dataset", """What the slide shows: image counts by class and three real crops.
What I should say: The release has 1,386 images because the rotated half repeats the aligned half. Detection uses the 693 images that have boxes. Our test split is 108 of those, with 477 boxes. Every image has one defect class.
Why it matters: The proposal mixed this set with DeepPCB. DeepPCB is a different 1,500-pair dataset and we did not train on it.
Transition: Now the path from a camera to a decision, including the parts we did not build.
Source: Huang et al. 2020, DOI 10.1049/joe.2019.1183. results/dataset_report.json.""")

    # 6
    slide = blank(prs)
    add_text(slide, "Where a measurement stops and a control begins", Inches(0.4), Inches(0.22), Inches(12), Inches(0.5), 30, True, NAVY)
    steps = [
        ("Camera and lighting", BLUE, "Assumed"),
        ("Image-quality gate", GOLD, "Not built"),
        ("Letterbox to 640", GREEN, "Measured"),
        ("YOLOv5u-s detector", GREEN, "Measured"),
        ("Box, class, confidence", GREEN, "Measured"),
        ("Decision threshold 0.25", GREEN, "Measured"),
        ("Human review or release", BLUE, "Assumed"),
        ("Audit log and monitoring", GOLD, "Not built"),
    ]
    top = 0.85
    for label, color, tag in steps:
        add_rect(slide, Inches(0.4), Inches(top), Inches(8.5), Inches(0.62), color)
        add_text(slide, label, Inches(0.6), Inches(top + 0.08), Inches(5.6), Inches(0.46), 20, True, WHITE)
        add_text(slide, tag, Inches(6.3), Inches(top + 0.08), Inches(2.4), Inches(0.46), 16, False, WHITE, PP_ALIGN.RIGHT)
        top += 0.7
    add_rect(slide, Inches(9.2), Inches(1.1), Inches(3.7), Inches(4.6), PALE, GREEN)
    add_text(slide, "Green  ran in this audit\n\nBlue  assumed cell\n\nGold  recommended, not built", Inches(9.4), Inches(1.4), Inches(3.3), Inches(4.0), 18, False, NAVY)
    footer(slide, "Only the green blocks were executed. Mean single-image call time was 38.9 ms, including overhead.")
    remember("Pipeline", """What the slide shows: eight stages, colored by what we actually ran.
What I should say: Green is the experiment: resize, the frozen detector, the score, and the 0.25 threshold. Blue is the cell we assume when we talk about governance. Gold is a control we recommend and did not implement. I should not talk as if the log or the quality gate already exists.
Why it matters: The rest of the control plan hangs on this distinction.
Transition: Those stages are also the places an input change, or a file change, can enter.
Source: results/baseline_metrics.csv for the timing. Ultralytics input size 640.""")

    # 7
    slide = blank(prs)
    add_text(slide, "A changed image can become a wrong accept", Inches(0.4), Inches(0.2), Inches(12), Inches(0.5), 30, True, NAVY)
    add_rect(slide, Inches(4.55), Inches(2.7), Inches(4.2), Inches(1.5), NAVY)
    add_text(slide, "Frozen detector\nthen a threshold", Inches(4.7), Inches(2.95), Inches(3.9), Inches(1.1), 20, True, WHITE, PP_ALIGN.CENTER)
    surfaces = [
        (0.4, 1.05, "Camera and light", "Literature", GOLD),
        (4.7, 1.05, "Image input", "Measured", GREEN),
        (9.0, 1.05, "Labels and weights", "Not tested", BLUE),
        (0.4, 4.7, "Decision threshold", "Fixed, not attacked", BLUE),
        (4.7, 4.7, "Human review", "Assumed", BLUE),
        (9.0, 4.7, "Monitoring and logs", "Not built", GOLD),
    ]
    for left, top, title, tag, color in surfaces:
        add_rect(slide, Inches(left), Inches(top), Inches(3.7), Inches(1.25), WHITE, color)
        add_text(slide, title, Inches(left + 0.15), Inches(top + 0.12), Inches(3.4), Inches(0.5), 18, True, NAVY)
        add_text(slide, tag, Inches(left + 0.15), Inches(top + 0.62), Inches(3.4), Inches(0.4), 16, False, color)
    add_text(slide, "Measured path: a worse image, a miss or a weaker score, then an accept that should have been a hold.", Inches(0.45), Inches(6.2), Inches(12.4), Inches(0.7), 18, False, INK)
    footer(slide, "Weight edits, label poisoning, and a live API were not run. Eykholt et al. 2018 and Lee and Kolter 2019 motivate the physical case.")
    remember("Threat model", """What the slide shows: six surfaces around the detector, tagged by evidence.
What I should say: The only surface we changed was the image. Camera access is supported by the physical-attack papers, not by a camera trial of our own. Labels, weights, the reviewer, and the log are scenarios. The arrow that matters is image, then miss, then a board that moves forward.
Why it matters: A threat model that marks everything as an attack overclaims the experiment.
Transition: Here is the procedure that produced the measured part.
Source: MITRE ATLAS AML.T0041 for physical environment access. Eykholt et al., arXiv:1807.07769. Lee and Kolter, arXiv:1906.11897.""")

    # 8
    slide = blank(prs)
    add_text(slide, "One model. One change at a time.", Inches(0.4), Inches(0.22), Inches(12), Inches(0.5), 32, True, NAVY)
    timeline = ["Clean test", "Freeze weights", "One edit", "Same detector", "Compare", "Score the drop", "Name the risk"]
    for index, label in enumerate(timeline):
        left = 0.3 + index * 1.86
        add_rect(slide, Inches(left), Inches(1.15), Inches(1.7), Inches(1.15), NAVY if index < 5 else GREEN)
        add_text(slide, label, Inches(left + 0.06), Inches(1.4), Inches(1.58), Inches(0.75), 16, True, WHITE, PP_ALIGN.CENTER)
    families = ["Noise", "Blur", "Brightness", "JPEG", "Rotation", "Scale", "Occlusion on the defect"]
    left = 0.32
    for label in families:
        width = 1.95 if label.startswith("Occlusion") else 1.62
        add_rect(slide, Inches(left), Inches(2.75), Inches(width), Inches(0.72), PALE, GREEN)
        add_text(slide, label, Inches(left + 0.04), Inches(2.88), Inches(width - 0.06), Inches(0.48), 15, True, NAVY, PP_ALIGN.CENTER)
        left += width + 0.08
    add_text(slide, "Three intensities for each family. Boxes are rewritten after rotation and scale. The cover and the noise keep the original boxes. Test images were never used for training.", Inches(0.45), Inches(3.8), Inches(12.3), Inches(1.2), 20, False, INK)
    add_text(slide, "Recall change = (perturbed − clean) / clean × 100.", Inches(0.45), Inches(5.2), Inches(12), Inches(0.5), 22, True, NAVY)
    footer(slide, "108 test images, 477 boxes. Match: same class, IoU at least 0.50, confidence at least 0.25.")
    remember("Design", """What the slide shows: the sequence and the seven families.
What I should say: We did not retrain between conditions. Each family has three levels. Rotation moves the board, so the boxes move with it. The gray cover is a sensitivity probe on the defect, not an optimized patch.
Why it matters: If I skip the formula, the 73 percent later has no definition.
Transition: Show what four of those conditions look like on one hole.
Source: src/generate_perturbations.py and src/calculate_metrics.py.""")

    # 9
    slide = blank(prs)
    add_text(slide, "One hole, four inputs", Inches(0.4), Inches(0.18), Inches(12), Inches(0.45), 32, True, NAVY)
    order = [("none", "Original"), ("noise", "Noise, σ = 25"), ("rotation", "Rotation, 12°"), ("occlusion", "Cover, ~30% of the box")]
    left = 0.28
    for key, label in order:
        add_picture(slide, SLIDES / f"panel_{key}.jpg", Inches(left), Inches(0.8), Inches(3.15), Inches(4.3))
        result = by_key[key]["result"]
        color = RED if result == "Missed" else NAVY
        add_text(slide, label, Inches(left), Inches(5.2), Inches(3.15), Inches(0.7), 16, True, NAVY, PP_ALIGN.CENTER)
        add_text(slide, result, Inches(left), Inches(5.85), Inches(3.15), Inches(0.45), 20, True, color, PP_ALIGN.CENTER)
        left += 3.26
    add_text(slide, "Green box: annotation. Red box: prediction. This hole survived noise at confidence 0.34. The cover removed it. Dataset-wide rates are on the next slides.", Inches(0.4), Inches(6.4), Inches(12.5), Inches(0.6), 16, False, INK)
    footer(slide, "Image 01_missing_hole_09. Noise level 2 on this image found 2 of 3 holes. The cover at side fraction 0.55 found 0 of 3.")
    remember("Example images", """What the slide shows: the same hole under four conditions, with the model's own score.
What I should say: On this one hole the clean score is 0.81. Noise drops that score to 0.34 but the hole is still found. A 12-degree rotation still finds it at 0.80. The gray cover, about 30 percent of the box area, removes the detection. I should not say this single hole is the 73 percent dataset drop. That number is the next slide.
Why it matters: The audience can see the failure instead of only hearing a rate.
Transition: First, the clean score those drops are measured against.
Source: panel_results.json from one forward pass of results/best.pt. Per-image counts in results/perturbation_per_image.csv.""")

    # 10
    slide = blank(prs)
    add_text(slide, "Clean test: found, but not tightly localized", Inches(0.4), Inches(0.18), Inches(12.4), Inches(0.5), 30, True, NAVY)
    add_picture(slide, SLIDES / "baseline_scores.png", Inches(0.2), Inches(0.75), Inches(8.6), Inches(5.6))
    add_text(slide, "108 images\n477 defects\n49 misses\n7 wrong-class overlaps", Inches(8.8), Inches(1.3), Inches(4.1), Inches(2.4), 22, True, NAVY)
    add_text(slide, "Green bars are detection scores. Navy bars are localization. The detector found many defects, but localization was weaker than mAP@0.5 suggests.", Inches(8.8), Inches(4.0), Inches(4.1), Inches(2.4), 18, False, INK)
    footer(slide, "results/baseline_metrics.csv. Class-aware IoU 0.50. mAP is our 101-point implementation, not a COCO API call.")
    remember("Baseline", """What the slide shows: seven clean-test scores and the miss count.
What I should say: Precision 0.924, recall 0.897, F1 0.911, mAP at 0.5 is 0.921. That looks strong. mAP from 0.5 to 0.95 is 0.455, and the mean overlap of the hits is 0.760. So the boxes clear 0.5 and then fall off. Of 477 defects, 49 were missed. Only 7 overlaps had the wrong class, so the usual clean error is a miss, not a relabel.
Why it matters: A 0.92 mAP would be the end of a benchmark paper. It is the start of this audit.
Transition: Keep that 0.897 recall in mind. The next slide moves it.
Source: results/baseline_metrics.csv and results/per_class_metrics.csv. Lin et al., ECCV 2014, for the COCO AP tradition.""")

    # 11
    slide = blank(prs)
    add_text(slide, "Noise and a cover move the result. Blur does not.", Inches(0.35), Inches(0.15), Inches(12.5), Inches(0.48), 28, True, NAVY)
    add_picture(slide, SLIDES / "recall_lines.png", Inches(0.05), Inches(0.65), Inches(8.7), Inches(6.2))
    cards = [
        ("0.897", "Clean recall", NAVY, PALE),
        ("−73%", "Noise level 2\nrecall change", RED, PALE_RED),
        ("0.036", "Recall after a cover\non ~30% of the box", RED, PALE_RED),
    ]
    top = 1.15
    for value, label, color, fill in cards:
        add_rect(slide, Inches(8.85), Inches(top), Inches(4.1), Inches(1.55), fill, color)
        add_text(slide, value, Inches(9.0), Inches(top + 0.08), Inches(3.8), Inches(0.6), 28, True, color)
        add_text(slide, label, Inches(9.0), Inches(top + 0.7), Inches(3.8), Inches(0.7), 16, False, INK)
        top += 1.7
    footer(slide, "Recall at noise σ=25 is 0.241. Occlusion side fraction 0.55 covers about 30% of each box. Blur kernel 15 recall is 0.927.")
    remember("Main result", """What the slide shows: recall against intensity, with the three numbers I want remembered.
What I should say: Clean recall is 0.897. At noise standard deviation 25, recall falls to 0.241, a 73 percent reduction. Covering about 30 percent of each defect box drops recall to 0.036. Rotation declines more slowly, to 0.672 at 12 degrees. Blur, JPEG, and brightness stay near the clean line. A 15-pixel blur on a 3,000-pixel image is mild after the 640 resize, so I should not say blur is harmless in general.
Why it matters: This is the evidence slide. Everything after it interprets these curves.
Transition: The average hides which defect classes fail.
Source: results/perturbation_metrics.csv. Percentage change formula on the design slide.""")

    # 12
    slide = blank(prs)
    add_text(slide, "Spurs and extra copper fail before missing holes", Inches(0.4), Inches(0.15), Inches(12.4), Inches(0.48), 28, True, NAVY)
    add_picture(slide, SLIDES / "class_heatmap.png", Inches(0.05), Inches(0.7), Inches(8.5), Inches(6.15))
    add_text(slide, "Under noise, spur recall is 0 and spurious copper is 0.01. Missing-hole recall stays 0.87.", Inches(8.55), Inches(1.2), Inches(4.4), Inches(1.6), 18, False, INK)
    add_text(slide, "A cover on the defect drives five classes to 0. Only spur keeps any recall, at 0.21.", Inches(8.55), Inches(3.0), Inches(4.4), Inches(1.5), 18, False, INK)
    add_text(slide, "The usual failure is a miss. Clean test: 49 misses, 7 wrong-class overlaps.", Inches(8.55), Inches(4.7), Inches(4.4), Inches(1.5), 18, False, INK)
    footer(slide, "Heatmap values are recall. Noise and cover are level 2. Rotation is 12 degrees. results/perturbation_per_class.csv.")
    remember("Per class", """What the slide shows: recall by class for the clean test, moderate noise, the middle cover, and a 12-degree rotation.
What I should say: Missing holes and shorts start near 0.99. Under noise, spurs go to zero and spurious copper goes to 0.01, while missing-hole recall is still 0.87. The cover is harsher: five classes go to zero, and spur is the only class with recall left, 0.21. I should not call every class equally fragile. The dominant error is still a miss. Wrong class was uncommon on the clean test.
Why it matters: A single recall number would hide that thin copper defects fail first.
Transition: Turn that miss into the operational chain, and keep the chain labeled as measured or possible.
Source: results/perturbation_per_class.csv and results/baseline_metrics.csv.""")

    # 13
    slide = blank(prs)
    add_text(slide, "From a changed pixel to a board that should have stopped", Inches(0.35), Inches(0.2), Inches(12.6), Inches(0.55), 28, True, NAVY)
    chain = [
        ("Input change", "Measured", GREEN),
        ("Weaker score\nor a miss", "Measured", GREEN),
        ("False negative", "Measured", GREEN),
        ("Board moves on", "Possible", GOLD),
        ("Rework, return,\nor a bad lot", "Possible", GOLD),
    ]
    for index, (title, tag, color) in enumerate(chain):
        left = 0.3 + index * 2.6
        add_rect(slide, Inches(left), Inches(1.5), Inches(2.35), Inches(1.7), color)
        add_text(slide, title, Inches(left + 0.08), Inches(1.65), Inches(2.2), Inches(0.9), 18, True, WHITE, PP_ALIGN.CENTER)
        add_text(slide, tag, Inches(left + 0.08), Inches(2.6), Inches(2.2), Inches(0.4), 14, False, WHITE, PP_ALIGN.CENTER)
    add_rect(slide, Inches(0.4), Inches(3.7), Inches(6.1), Inches(2.7), PALE, GREEN)
    add_text(slide, "Measured in this audit", Inches(0.6), Inches(3.85), Inches(5.7), Inches(0.4), 18, True, GREEN)
    add_text(slide, "Noise, a cover on the defect, and rotation changed recall, confidence, or both. Class swaps were uncommon.", Inches(0.6), Inches(4.4), Inches(5.7), Inches(1.6), 18, False, INK)
    add_rect(slide, Inches(6.8), Inches(3.7), Inches(6.1), Inches(2.7), PALE_GOLD, GOLD)
    add_text(slide, "Potential operational consequence", Inches(7.0), Inches(3.85), Inches(5.7), Inches(0.4), 18, True, GOLD)
    add_text(slide, "No production incident was observed. A miss matters only if a person treats the score as an accept.", Inches(7.0), Inches(4.4), Inches(5.7), Inches(1.6), 18, False, INK)
    footer(slide, "Impact scores in the risk register are judgments. They are not measured dollar losses.")
    remember("Cause and effect", """What the slide shows: a five-step chain, with the last two steps marked possible rather than observed.
What I should say: We measured the left side: the image changed, scores fell or boxes disappeared, and the false-negative rate rose. We did not watch a factory accept a bad board. Rework and a customer return are what that miss could cost if the cell auto-accepts. I should say "could," not "did."
Why it matters: This is the line between an experiment and a governance claim.
Transition: ATLAS is how we name the techniques, and NIST is how we would manage them.
Source: results/perturbation_metrics.csv. NIST AI RMF, NIST AI 100-1, DOI 10.6028/NIST.AI.100-1.""")

    # 14
    slide = blank(prs)
    add_text(slide, "Name the technique. Then name the control.", Inches(0.4), Inches(0.16), Inches(12.4), Inches(0.45), 28, True, NAVY)
    atlas = [
        ("AML.T0043", "Craft Adversarial Data", "Measured in experiment", GREEN),
        ("AML.T0041", "Physical Environment Access", "Supported by literature", GOLD),
        ("AML.T0015", "Evade AI Model", "Scenario only", BLUE),
        ("AML.T0031", "Erode AI Model Integrity", "Scenario only", BLUE),
        ("AML.T0018", "Manipulate AI Model", "Scenario only", BLUE),
        ("AML.T0020", "Training Data Poisoning", "Scenario only", BLUE),
    ]
    top = 0.75
    for ident, name, level, color in atlas:
        add_text(slide, ident, Inches(0.35), Inches(top), Inches(1.7), Inches(0.9), 15, True, NAVY)
        add_text(slide, name, Inches(2.05), Inches(top), Inches(2.7), Inches(0.9), 15, False, INK)
        add_text(slide, level, Inches(4.7), Inches(top), Inches(2.35), Inches(0.9), 15, True, color)
        top += 0.95
    add_text(slide, "Controls for the set. Not one per row.", Inches(7.2), Inches(0.7), Inches(5.7), Inches(0.4), 16, True, NAVY)
    controls = [
        "Image-quality gate before inference",
        "Hold a low-confidence board for a person",
        "Watch confidence, recall, and misses",
        "Hash the weights and log the decision",
        "Retest after a camera or light change",
    ]
    top = 1.2
    for item in controls:
        add_rect(slide, Inches(7.2), Inches(top), Inches(5.7), Inches(0.95), PALE, GREEN)
        add_text(slide, item, Inches(7.4), Inches(top + 0.22), Inches(5.35), Inches(0.55), 16, False, NAVY)
        top += 1.1
    footer(slide, "ATLAS content 2026.10, modified 28 Oct 2026. T0043 here is manual image edits, not an optimized attack.")
    remember("ATLAS and controls", """What the slide shows: six ATLAS names with an evidence label, and five controls.
What I should say: Craft Adversarial Data, including manual modification, is the name for the edits we actually ran. Physical Environment Access is in the literature; we did not touch a real camera. Evade AI Model, eroding integrity, swapping weights, and poisoning labels are scenarios. The controls on the right do not erase those risks. They make a miss harder to auto-accept. NIST's frame for that plan is Govern, Map, Measure, Manage.
Why it matters: The professor asked for evidence-first mapping, not a list of every ATLAS ID.
Transition: Close with the release rule that follows from the curves.
Source: github.com/mitre-atlas/atlas-data ATLAS-2026.10.yaml. Pages are atlas.mitre.org/techniques/ plus the ID. NIST AI 100-1.""")

    # 15
    slide = blank(prs, dark=True)
    add_text(slide, "Release decision: conditional deployment only", Inches(0.45), Inches(0.22), Inches(12.3), Inches(0.5), 28, True, WHITE)
    gates = [
        "Do not auto-accept an image outside the tested range.",
        "Hold a low-confidence prediction for a person.",
        "Monitor per-class recall and false negatives.",
        "Log the weight hash, the image, the score, and the decision.",
        "Repeat the robustness test after a camera, light, or board change.",
        "Keep a second look for open, short, and missing-hole defects.",
    ]
    top = 0.85
    for gate in gates:
        add_text(slide, gate, Inches(0.55), Inches(top), Inches(7.6), Inches(0.42), 16, False, WHITE)
        top += 0.42
    add_text(slide, "1  Clean accuracy is not a release test.\n2  Noise and a cover on the defect caused real misses.\n3  Use the gates above before any automatic accept.", Inches(0.5), Inches(3.5), Inches(7.7), Inches(1.7), 16, True, RGBColor(0xD5, 0xE4, 0xDA))
    add_rect(slide, Inches(8.4), Inches(0.95), Inches(4.5), Inches(5.5), RGBColor(0x14, 0x2C, 0x4E))
    add_text(slide, "Limits", Inches(8.6), Inches(1.1), Inches(4.1), Inches(0.4), 18, True, GREEN)
    add_text(slide, "Public synthetic images.\nDigital edits, not a physical attack.\nOne checkpoint, one split.\nNo factory deployment claim.\nThis checkpoint fails a strict per-class noise bar.", Inches(8.6), Inches(1.6), Inches(4.1), Inches(4.4), 16, False, WHITE)
    footer(slide, "Suggested noise bar: level-2 recall drop no larger than 0.10 on every class. Spur and spurious copper miss it.", dark=True)
    remember("Release decision", """What the slide shows: a conditional release, six gates, three conclusions, and the limits.
What I should say: I would not turn automatic accept on for this checkpoint. Clean recall of 0.897 coexists with a 73 percent recall drop under moderate noise and a near-total miss when the defect is covered. The gates are how an organization would use the model anyway: reject bad frames, hold weak scores, watch each class, log the file that made the call, and retest when the camera changes. The limits box is part of the answer. These are research images, the edits were digital, and we did not see this file run in a factory.
Why it matters: It is the decision the audit was for.
Transition: Stop. Take questions on the noise curve, the cover, or the factory limitation.
Source: results/perturbation_per_class.csv for the per-class noise bar. NIST AI RMF Playbook, nist.gov.""")

    drop_theme_styles(prs)
    out = ROOT / "presentation" / "final_presentation.pptx"
    prs.save(out)
    lines = ["# Speaker notes", "", "Keynote cannot import the notes pages that python-pptx writes, so these notes live in this file.", ""]
    for index, (title, note) in enumerate(NOTES, start=1):
        lines.append(f"## Slide {index} — {title}")
        lines.append("")
        lines.append(note.strip())
        lines.append("")
    (ROOT / "presentation" / "speaker_notes.md").write_text("\n".join(lines))
    print(out)
    print("slides", len(NOTES))


if __name__ == "__main__":
    main()
