"""Build the risk register, assurance matrix, control coverage, and ATLAS table.

Likelihood for image-quality threats is derived from the measured recall drop
at the middle intensity level. Impact scores are engineering judgments about
the consequence of a missed defect class, not measured factory losses. Threats
that were not executed in the laboratory are labeled scenario_assessment.
"""

from __future__ import annotations

import pandas as pd

from config import RESEARCH, RESULTS, TABLES

ATLAS_ROWS = [
    {
        "technique_id": "AML.T0043",
        "technique_name": "Craft Adversarial Data",
        "tactic_id": "AML.TA0001",
        "tactic": "AI Attack Adaptation",
        "subtechnique_id": "AML.T0043.003",
        "subtechnique_name": "Manual Modification",
        "maturity": "Realized",
        "evidence_type": "controlled laboratory sensitivity test, not an optimized attack",
        "why_it_applies": "The audit changes test images with blur, noise, compression, illumination, and a gray occlusion over annotated defects, then measures missed detections.",
        "affected_component": "Model input",
        "mitigation_id": "AML.M0015",
        "mitigation_name": "Predictive AI Adversarial Input Detection",
        "official_url": "https://atlas.mitre.org/techniques/AML.T0043",
        "data_source": "MITRE ATLAS content 2026.10, dist/v6/ATLAS-2026.10.yaml",
    },
    {
        "technique_id": "AML.T0015",
        "technique_name": "Evade AI Model",
        "tactic_id": "AML.TA0011",
        "tactic": "Impact",
        "subtechnique_id": "",
        "subtechnique_name": "",
        "maturity": "Realized",
        "evidence_type": "plausible operational consequence of the measured false-negative increase; not a demonstrated attack on a factory",
        "why_it_applies": "A missed defect is the inspection-system analogue of a missed detection. ATLAS also places this technique under Initial Access and Defense Evasion for other AI uses; the relevant placement here is Impact.",
        "affected_component": "Predictions and production decision",
        "mitigation_id": "AML.M0003",
        "mitigation_name": "Predictive AI Model Hardening",
        "official_url": "https://atlas.mitre.org/techniques/AML.T0015",
        "data_source": "MITRE ATLAS content 2026.10; tactic placement from the distributed matrix in dist/ATLAS.yaml 5.6.0, which lists AML.TA0004, AML.TA0007, and AML.TA0011",
    },
    {
        "technique_id": "AML.T0041",
        "technique_name": "Physical Environment Access",
        "tactic_id": "AML.TA0000",
        "tactic": "AI Model Access",
        "subtechnique_id": "",
        "subtechnique_name": "",
        "maturity": "Demonstrated",
        "evidence_type": "literature-supported and scenario; this project did not physically access a camera",
        "why_it_applies": "Brightness, blur, and occlusion approximate changes an actor with access to lighting, the lens, or the board surface could introduce. The laboratory changes were digital.",
        "affected_component": "Camera and image acquisition",
        "mitigation_id": "AML.M0009",
        "mitigation_name": "Predictive AI Multi-Sensor Fusion",
        "official_url": "https://atlas.mitre.org/techniques/AML.T0041",
        "data_source": "MITRE ATLAS content 2026.10",
    },
    {
        "technique_id": "AML.T0040",
        "technique_name": "AI Model Inference API Access",
        "tactic_id": "AML.TA0000",
        "tactic": "AI Model Access",
        "subtechnique_id": "",
        "subtechnique_name": "",
        "maturity": "Realized",
        "evidence_type": "scenario_assessment",
        "why_it_applies": "An assumed inspection server that accepts images would let an adversary verify which degradations suppress detections. This project used an offline copy, not a networked API.",
        "affected_component": "Inference server",
        "mitigation_id": "AML.M0004",
        "mitigation_name": "Limit AI Service Query Volume and Rate",
        "official_url": "https://atlas.mitre.org/techniques/AML.T0040",
        "data_source": "MITRE ATLAS content 2026.10",
    },
    {
        "technique_id": "AML.T0042",
        "technique_name": "Verify Attack",
        "tactic_id": "AML.TA0001",
        "tactic": "AI Attack Adaptation",
        "subtechnique_id": "",
        "subtechnique_name": "",
        "maturity": "Realized",
        "evidence_type": "method of this audit, performed by the evaluators on an offline copy",
        "why_it_applies": "The audit compares original and perturbed predictions on a fixed checkpoint. That is the defensive form of verifying whether an input change alters the model. It is not an attack against a victim system.",
        "affected_component": "Offline model copy",
        "mitigation_id": "AML.M0001",
        "mitigation_name": "Limit Model Artifact Release",
        "official_url": "https://atlas.mitre.org/techniques/AML.T0042",
        "data_source": "MITRE ATLAS content 2026.10",
    },
    {
        "technique_id": "AML.T0044",
        "technique_name": "Full AI Model Access",
        "tactic_id": "AML.TA0000",
        "tactic": "AI Model Access",
        "subtechnique_id": "",
        "subtechnique_name": "",
        "maturity": "Demonstrated",
        "evidence_type": "scenario_assessment",
        "why_it_applies": "The fine-tuned checkpoint is an ordinary file. An actor who copies it obtains architecture, weights, and the class list. This audit did not steal a production model.",
        "affected_component": "Model weights",
        "mitigation_id": "AML.M0005",
        "mitigation_name": "Control Access to AI Models and Data at Rest",
        "official_url": "https://atlas.mitre.org/techniques/AML.T0044",
        "data_source": "MITRE ATLAS content 2026.10",
    },
    {
        "technique_id": "AML.T0018",
        "technique_name": "Manipulate AI Model",
        "tactic_id": "AML.TA0006",
        "tactic": "Persistence",
        "subtechnique_id": "AML.T0018.000",
        "subtechnique_name": "Poison AI Model",
        "maturity": "Demonstrated",
        "evidence_type": "scenario_assessment",
        "why_it_applies": "Unauthorized replacement of the checkpoint would change detections without changing the camera. Not executed in this project.",
        "affected_component": "Model weights",
        "mitigation_id": "AML.M0014",
        "mitigation_name": "Verify AI Artifacts",
        "official_url": "https://atlas.mitre.org/techniques/AML.T0018",
        "data_source": "MITRE ATLAS content 2026.10. Tactic Persistence is AML.TA0006 in the 5.6.0 matrix; the technique is also associated with AI Attack Adaptation.",
    },
    {
        "technique_id": "AML.T0020",
        "technique_name": "Training Data Poisoning",
        "tactic_id": "AML.TA0003",
        "tactic": "Resource Development",
        "subtechnique_id": "",
        "subtechnique_name": "",
        "maturity": "Realized",
        "evidence_type": "scenario_assessment",
        "why_it_applies": "The public dataset is synthetic and label-driven. Corrupted boxes or labels would be inherited by a fine-tune. This audit did not poison the training split.",
        "affected_component": "Dataset and annotations",
        "mitigation_id": "AML.M0007",
        "mitigation_name": "Sanitize Training Data",
        "official_url": "https://atlas.mitre.org/techniques/AML.T0020",
        "data_source": "MITRE ATLAS content 2026.10. The 2026.10 record name is Training Data Poisoning.",
    },
    {
        "technique_id": "AML.T0059",
        "technique_name": "Erode Dataset Integrity",
        "tactic_id": "AML.TA0011",
        "tactic": "Impact",
        "subtechnique_id": "",
        "subtechnique_name": "",
        "maturity": "Demonstrated",
        "evidence_type": "scenario_assessment",
        "why_it_applies": "Annotation damage would reduce the usefulness of the inspection dataset and waste review effort. Not executed.",
        "affected_component": "Dataset and annotations",
        "mitigation_id": "AML.M0007",
        "mitigation_name": "Sanitize Training Data",
        "official_url": "https://atlas.mitre.org/techniques/AML.T0059",
        "data_source": "MITRE ATLAS content 2026.10",
    },
    {
        "technique_id": "AML.T0031",
        "technique_name": "Erode AI Model Integrity",
        "tactic_id": "AML.TA0011",
        "tactic": "Impact",
        "subtechnique_id": "",
        "subtechnique_name": "",
        "maturity": "Realized",
        "evidence_type": "plausible if measured degradation were repeated in production without monitoring",
        "why_it_applies": "Repeated degraded inputs that increase misses can cause operators to stop trusting the detector or to miss real defects while chasing unstable scores.",
        "affected_component": "Monitoring and human approval",
        "mitigation_id": "AML.M0003",
        "mitigation_name": "Predictive AI Model Hardening",
        "official_url": "https://atlas.mitre.org/techniques/AML.T0031",
        "data_source": "MITRE ATLAS content 2026.10",
    },
    {
        "technique_id": "AML.T0010",
        "technique_name": "Supply Chain Compromise",
        "tactic_id": "AML.TA0004",
        "tactic": "Initial Access",
        "subtechnique_id": "AML.T0010.003",
        "subtechnique_name": "Model Repository",
        "maturity": "Realized",
        "evidence_type": "scenario_assessment",
        "why_it_applies": "The audited pipeline starts from a public pretrained checkpoint. A substituted upstream weight file would be inherited by fine-tuning. Not executed.",
        "affected_component": "Model update process",
        "mitigation_id": "AML.M0014",
        "mitigation_name": "Verify AI Artifacts",
        "official_url": "https://atlas.mitre.org/techniques/AML.T0010",
        "data_source": "MITRE ATLAS content 2026.10",
    },
]


def likelihood_from_drop(drop: float) -> int:
    if drop < 0.05:
        return 2
    if drop < 0.15:
        return 3
    if drop < 0.30:
        return 4
    return 5


def rating(score: int) -> str:
    if score >= 20:
        return "Critical"
    if score >= 13:
        return "High"
    if score >= 7:
        return "Medium"
    return "Low"


def measured_drop(frame: pd.DataFrame, family: str) -> float | None:
    part = frame[(frame["perturbation"] == family) & (frame["level"] == 2)]
    if part.empty or "pct_change_recall" not in part:
        return None
    # percentage change is negative when recall falls; convert to a positive drop in recall points
    base_recall = None
    return None


def recall_drop_points(metrics: pd.DataFrame, baseline_recall: float, family: str, level: int = 2) -> float | None:
    part = metrics[(metrics["perturbation"] == family) & (metrics["level"] == level)]
    if part.empty:
        return None
    return float(baseline_recall - part.iloc[0]["recall"])


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)
    atlas = pd.DataFrame(ATLAS_ROWS)
    atlas.to_csv(RESEARCH / "atlas_mapping.csv", index=False)
    atlas.to_csv(TABLES / "atlas_mapping.csv", index=False)

    metrics_path = RESULTS / "perturbation_metrics.csv"
    baseline_path = RESULTS / "baseline_metrics.csv"
    metrics = pd.read_csv(metrics_path) if metrics_path.exists() else None
    baseline_recall = None
    if baseline_path.exists():
        baseline_recall = float(pd.read_csv(baseline_path).iloc[0]["recall"])

    def L(family: str, default: int, basis: str) -> tuple[int, str]:
        if metrics is None or baseline_recall is None:
            return default, "scenario_assessment_metrics_unavailable"
        drop = recall_drop_points(metrics, baseline_recall, family, 2)
        if drop is None:
            return default, basis
        return likelihood_from_drop(drop), "experiment_level2_recall_drop"

    image_risks = [
        ("R1", "Additive sensor noise hides defects", "gaussian_noise", 4),
        ("R2", "Localized obstruction over an annotated defect suppresses detection", "localized_occlusion", 4),
        ("R3", "Global brightness shift changes detections", "brightness", 3),
        ("R4", "JPEG compression removes defect evidence", "jpeg", 3),
        ("R5", "In-plane rotation moves defects relative to the learned view", "rotation", 3),
    ]
    rows = []
    for risk_id, description, family, impact in image_risks:
        likelihood, basis = L(family, 3, "scenario_assessment")
        score = likelihood * impact
        rows.append(
            {
                "risk_id": risk_id,
                "threat": description,
                "preconditions": "Image reaches inference without a quality gate.",
                "attack_surface": "Camera, lighting, or image pipeline",
                "adversary_capability": "Ability to alter acquisition or to introduce ordinary degradation; no model-file access required.",
                "affected_component": "Model input and predictions",
                "expected_model_failure": "Lower recall, higher false-negative rate, lower confidence, or lower IoU.",
                "operational_consequence": "A defective board can be accepted, or a good board can be sent to manual review.",
                "likelihood": likelihood,
                "impact": impact,
                "risk_score": score,
                "risk_rating": rating(score),
                "evidence_basis": basis,
                "detection_method": "Image-quality checks and per-class recall monitoring.",
                "preventive_controls": "Fixed exposure, lens cleanliness, quality gate before inference.",
                "detective_controls": "Blur, brightness, and compression monitors; confidence and false-negative alerts.",
                "corrective_controls": "Hold the board, human review, restore the validated imaging setup.",
                "residual_risk": "A degradation inside the accepted quality range can still reduce recall. The control does not eliminate that risk.",
            }
        )

    scenario = [
        ("R6", "Unauthorized modification of model weights", "Model weights", 3, 5),
        ("R7", "Training-data or annotation corruption", "Dataset and annotations", 2, 4),
        ("R8", "Distribution shift after a camera, lighting, board, or process change", "Deployment context", 4, 4),
        ("R9", "Confidence-score misuse or an unreviewed threshold change", "Decision rule", 3, 4),
        ("R10", "Monitoring failure and human overreliance", "Human approval and logs", 3, 4),
    ]
    for risk_id, description, surface, likelihood, impact in scenario:
        score = likelihood * impact
        rows.append(
            {
                "risk_id": risk_id,
                "threat": description,
                "preconditions": "The stated asset is writable, unmonitored, or treated as authoritative.",
                "attack_surface": surface,
                "adversary_capability": "Depends on the asset. These rows were not executed as experiments.",
                "affected_component": surface,
                "expected_model_failure": "Systematic misses, stale performance, or a silent threshold change.",
                "operational_consequence": "Inspection decisions diverge from the validated model without a recorded reason.",
                "likelihood": likelihood,
                "impact": impact,
                "risk_score": score,
                "risk_rating": rating(score),
                "evidence_basis": "scenario_assessment",
                "detection_method": "Checksum verification, dataset review, drift monitors, and dual control on threshold changes.",
                "preventive_controls": "Access control, signed artifacts, change management.",
                "detective_controls": "Audit logs, recall dashboards, out-of-distribution checks.",
                "corrective_controls": "Rollback to the last validated checkpoint and revalidation.",
                "residual_risk": "A knowledgeable insider or a missed process change can still defeat a single control.",
            }
        )

    register = pd.DataFrame(rows)
    register.to_csv(RESULTS / "risk_register.csv", index=False)
    register.to_csv(TABLES / "risk_register.csv", index=False)

    controls = [
        "image_quality_gate",
        "confidence_monitor",
        "per_class_recall_monitor",
        "human_review",
        "artifact_integrity",
        "change_management",
        "redundant_inspection",
    ]
    coverage_map = {
        "R1": [1, 1, 1, 1, 0, 1, 1],
        "R2": [1, 1, 1, 1, 0, 0, 1],
        "R3": [1, 1, 1, 1, 0, 1, 0],
        "R4": [1, 1, 1, 1, 0, 0, 1],
        "R5": [1, 1, 1, 1, 0, 1, 0],
        "R6": [0, 1, 1, 1, 1, 1, 1],
        "R7": [0, 0, 1, 1, 1, 1, 0],
        "R8": [1, 1, 1, 1, 0, 1, 1],
        "R9": [0, 1, 1, 1, 0, 1, 1],
        "R10": [1, 1, 1, 1, 0, 1, 1],
    }
    coverage = pd.DataFrame(
        [{"risk_id": key, **dict(zip(controls, values))} for key, values in coverage_map.items()]
    )
    coverage.to_csv(TABLES / "control_coverage.csv", index=False)

    assurance = [
        ("R1", "Recall and FNR under blur at the validated level", "Offline perturbation replay", "Recall drop at level 2 blur <= 0.10", "Quality engineer", "Each model release and quarterly", "Drop exceeds 0.10", "Hold deployment and retune imaging or review threshold"),
        ("R2", "Recall under localized occlusion", "Occlusion replay on the frozen test set", "Level-2 side fraction 0.55 does not drop recall by more than 0.15", "Model developer", "Each release", "Drop exceeds 0.15", "Require human review for low-confidence or partially occluded boards"),
        ("R3", "Recall under brightness and illumination", "Brightness and gradient replay", "Level-2 recall drop <= 0.10", "Process engineer", "After lighting maintenance", "Drop exceeds 0.10", "Restore exposure and revalidate"),
        ("R4", "Recall under JPEG and noise", "Compression and noise replay", "Level-2 recall drop <= 0.10", "Model developer", "Each release", "Drop exceeds 0.10", "Reject over-compressed frames"),
        ("R5", "Recall under small rotation and scale", "Geometric replay with transformed boxes", "Level-2 recall drop <= 0.10", "Vision engineer", "After fixture changes", "Drop exceeds 0.10", "Add a fixture check and revalidate"),
        ("R6", "Weight checksum matches the validated release", "Hash comparison at load", "Mismatch count = 0", "ML operations", "Every deployment", "Any mismatch", "Refuse to load and roll back"),
        ("R7", "Annotation audit sample", "Independent relabel of a sample", "Disagreement rate documented and below the accepted limit", "Data steward", "Before each training run", "Disagreement above the limit", "Quarantine the batch"),
        ("R8", "Input-distribution monitor", "Brightness, blur, and size statistics versus the validation window", "Share of out-of-window images below 5 percent in a shift", "Quality engineer", "Every shift", "Share exceeds 5 percent", "Stop automatic accept and revalidate"),
        ("R9", "Threshold and confidence log", "Compare the running threshold with the approved record", "Unapproved changes = 0", "Quality manager", "Weekly", "Any unapproved change", "Restore the approved threshold"),
        ("R10", "Human-review completion", "Audit log of low-confidence decisions", "Review completion = 100 percent of flagged boards", "Inspection supervisor", "Daily", "Any skipped review", "Quarantine the affected lot"),
    ]
    assurance_frame = pd.DataFrame(
        assurance,
        columns=[
            "risk_id",
            "evidence_required",
            "test_method",
            "acceptance_threshold",
            "owner",
            "review_frequency",
            "escalation_condition",
            "corrective_action",
        ],
    )
    assurance_frame.to_csv(TABLES / "assurance_matrix.csv", index=False)
    print(register[["risk_id", "likelihood", "impact", "risk_rating", "evidence_basis"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
