"""Draw the audit figures from measured CSV files.

If a required measurement file is missing, the corresponding figure is saved
with an explicit 'Illustrative example only' banner and is not treated as a
finding. Illustrative files are also listed in figures/figure_status.csv.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

from config import DISPLAY_NAMES, FIGURES, RESULTS, TABLES

NAVY = "#0B1F3A"
GREEN = "#1F8A4C"
GOLD = "#C4A35A"
RED = "#9B2335"
LIGHT = "#F4F7F5"
CMAP = LinearSegmentedColormap.from_list("pcb", ["#F7F4EF", "#7DCEA0", "#0B1F3A"])
RISK_CMAP = LinearSegmentedColormap.from_list("risk", ["#E8F6EE", "#F6E27A", "#9B2335"])


def style():
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.titlesize": 13,
            "axes.labelsize": 11,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": NAVY,
            "axes.labelcolor": NAVY,
            "xtick.color": NAVY,
            "ytick.color": NAVY,
            "text.color": NAVY,
            "axes.titleweight": "semibold",
        }
    )


def banner(ax, text: str):
    ax.text(
        0.5,
        0.5,
        text,
        transform=ax.transAxes,
        ha="center",
        va="center",
        fontsize=12,
        color=RED,
        fontweight="bold",
        bbox={"boxstyle": "round", "facecolor": "white", "edgecolor": RED, "alpha": 0.92},
    )


def save(fig, name: str):
    FIGURES.mkdir(parents=True, exist_ok=True)
    path = FIGURES / name
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path


def class_distribution(status_rows: list[dict]):
    path = TABLES / "dataset_summary_images.csv"
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    if not path.exists():
        ax.set_title("Dataset class distribution")
        banner(ax, "ILLUSTRATIVE EXAMPLE ONLY\nDataset summary was not produced")
        save(fig, "fig01_class_distribution.png")
        status_rows.append({"figure": "fig01_class_distribution.png", "status": "illustrative"})
        return
    frame = pd.read_csv(path)
    totals = frame.groupby("dominant_class")["n_images"].sum().reindex(list(DISPLAY_NAMES))
    labels = [DISPLAY_NAMES[k] for k in totals.index]
    ax.bar(labels, totals.values, color=GREEN, edgecolor=NAVY)
    ax.set_title("Annotated images by defect category")
    ax.set_ylabel("Number of images")
    ax.set_xlabel("Defect category")
    for label in ax.get_xticklabels():
        label.set_rotation(20)
        label.set_ha("right")
    ax.set_ylim(0, max(totals.values) * 1.2)
    note = "Source: HRIPCB aligned split (results/split_manifest.csv)."
    fig.text(0.01, 0.01, note, fontsize=8, color="#334155")
    save(fig, "fig01_class_distribution.png")
    status_rows.append({"figure": "fig01_class_distribution.png", "status": "measured"})


def baseline_chart(status_rows: list[dict]):
    path = RESULTS / "baseline_metrics.csv"
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    metrics = ["precision", "recall", "f1", "map50", "map50_95", "false_negative_rate"]
    labels = ["Precision", "Recall", "F1", "mAP@0.5", "mAP@0.5:0.95", "False-negative rate"]
    if not path.exists():
        ax.set_title("Baseline metric summary")
        banner(ax, "ILLUSTRATIVE EXAMPLE ONLY\nBaseline metrics were not measured")
        save(fig, "fig02_baseline_metrics.png")
        status_rows.append({"figure": "fig02_baseline_metrics.png", "status": "illustrative"})
        return
    row = pd.read_csv(path).iloc[0]
    values = [float(row[m]) for m in metrics]
    ax.bar(labels, values, color=[GREEN, GREEN, GREEN, NAVY, NAVY, RED], edgecolor=NAVY)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score (fraction)")
    ax.set_title("Baseline operating point and mAP on original test images")
    for label in ax.get_xticklabels():
        label.set_rotation(20)
        label.set_ha("right")
    fig.text(0.01, 0.01, "Source: results/baseline_metrics.csv. Confidence threshold 0.25, match IoU 0.50.", fontsize=8)
    save(fig, "fig02_baseline_metrics.png")
    status_rows.append({"figure": "fig02_baseline_metrics.png", "status": "measured"})


def line_chart(metric: str, ylabel: str, title: str, filename: str, status_rows: list[dict]):
    path = RESULTS / "perturbation_metrics.csv"
    catalog = RESULTS / "perturbation_catalog.csv"
    fig, ax = plt.subplots(figsize=(8.6, 5.0))
    if not path.exists():
        ax.set_title(title)
        banner(ax, "ILLUSTRATIVE EXAMPLE ONLY\nPerturbation metrics were not measured")
        save(fig, filename)
        status_rows.append({"figure": filename, "status": "illustrative"})
        return
    frame = pd.read_csv(path)
    intensities = None
    if catalog.exists():
        intensities = (
            pd.read_csv(catalog)[["perturbation", "level", "intensity", "unit"]]
            .drop_duplicates()
        )
    families = list(frame["perturbation"].unique())
    colors = plt.cm.tab10(np.linspace(0, 1, len(families)))
    for color, family in zip(colors, families):
        part = frame[frame["perturbation"] == family].sort_values("level")
        ax.plot(part["level"], part[metric], marker="o", label=family.replace("_", " "), color=color)
    if metric == "recall" and (RESULTS / "baseline_metrics.csv").exists():
        base = float(pd.read_csv(RESULTS / "baseline_metrics.csv").iloc[0]["recall"])
        ax.axhline(base, color=NAVY, linestyle="--", linewidth=1, label="baseline recall")
    if metric == "false_negative_rate" and (RESULTS / "baseline_metrics.csv").exists():
        base = float(pd.read_csv(RESULTS / "baseline_metrics.csv").iloc[0]["false_negative_rate"])
        ax.axhline(base, color=NAVY, linestyle="--", linewidth=1, label="baseline FNR")
    ax.set_xticks([1, 2, 3])
    ax.set_xlabel("Intensity level (1 = mild, 3 = strongest; units differ by family)")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend(fontsize=8, ncol=2, frameon=False)
    ax.set_ylim(0, 1.05)
    note = "Source: results/perturbation_metrics.csv."
    if intensities is not None:
        note += " Exact intensities are in results/perturbation_catalog.csv."
    fig.text(0.01, 0.01, note, fontsize=8)
    save(fig, filename)
    status_rows.append({"figure": filename, "status": "measured"})


def map_bars(status_rows: list[dict]):
    path = RESULTS / "perturbation_metrics.csv"
    fig, ax = plt.subplots(figsize=(9.0, 5.0))
    if not path.exists():
        ax.set_title("mAP@0.5 by perturbation")
        banner(ax, "ILLUSTRATIVE EXAMPLE ONLY")
        save(fig, "fig05_map_by_perturbation.png")
        status_rows.append({"figure": "fig05_map_by_perturbation.png", "status": "illustrative"})
        return
    frame = pd.read_csv(path)
    pivot = frame.pivot(index="perturbation", columns="level", values="map50")
    x = np.arange(len(pivot.index))
    width = 0.25
    for offset, level in zip((-width, 0, width), [1, 2, 3]):
        if level in pivot.columns:
            ax.bar(x + offset, pivot[level], width=width, label=f"Level {level}")
    if (RESULTS / "baseline_metrics.csv").exists():
        base = float(pd.read_csv(RESULTS / "baseline_metrics.csv").iloc[0]["map50"])
        ax.axhline(base, color=NAVY, linestyle="--", linewidth=1, label="baseline")
    ax.set_xticks(x)
    ax.set_xticklabels([name.replace("_", "\n") for name in pivot.index], fontsize=8)
    ax.set_ylabel("mAP@0.5")
    ax.set_ylim(0, 1.05)
    ax.set_title("mAP@0.5 across perturbation families and intensity levels")
    ax.legend(fontsize=8, frameon=False, ncol=4)
    fig.text(0.01, 0.01, "Source: results/perturbation_metrics.csv. 101-point interpolated AP, IoU 0.50.", fontsize=8)
    save(fig, "fig05_map_by_perturbation.png")
    status_rows.append({"figure": "fig05_map_by_perturbation.png", "status": "measured"})


def heatmap(status_rows: list[dict]):
    path = RESULTS / "perturbation_per_class.csv"
    fig, ax = plt.subplots(figsize=(9.2, 4.8))
    if not path.exists():
        ax.set_title("Per-class recall at strongest perturbation")
        banner(ax, "ILLUSTRATIVE EXAMPLE ONLY")
        save(fig, "fig08_class_robustness_heatmap.png")
        status_rows.append({"figure": "fig08_class_robustness_heatmap.png", "status": "illustrative"})
        return
    frame = pd.read_csv(path)
    strongest = frame[frame["level"] == frame["level"].max()]
    pivot = strongest.pivot(index="class_name", columns="perturbation", values="recall")
    pivot = pivot.reindex(list(DISPLAY_NAMES))
    image = ax.imshow(pivot.values, cmap=CMAP, vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(pivot.shape[1]))
    ax.set_xticklabels([c.replace("_", "\n") for c in pivot.columns], fontsize=8)
    ax.set_yticks(range(pivot.shape[0]))
    ax.set_yticklabels([DISPLAY_NAMES[i] for i in pivot.index])
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            value = pivot.values[i, j]
            if np.isfinite(value):
                ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=7, color="black")
    ax.set_title("Per-class recall at the strongest intensity of each perturbation")
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04, label="Recall")
    fig.text(0.01, 0.01, "Source: results/perturbation_per_class.csv. Operating point: confidence 0.25, IoU 0.50.", fontsize=8)
    save(fig, "fig08_class_robustness_heatmap.png")
    status_rows.append({"figure": "fig08_class_robustness_heatmap.png", "status": "measured"})


def confusion(status_rows: list[dict]):
    path = RESULTS / "baseline_confusion_long.csv"
    fig, ax = plt.subplots(figsize=(7.2, 5.6))
    labels = list(DISPLAY_NAMES) + ["missed"]
    keys = list(DISPLAY_NAMES) + ["missed"]
    if not path.exists():
        ax.set_title("Baseline class consistency")
        banner(ax, "ILLUSTRATIVE EXAMPLE ONLY")
        save(fig, "fig09_confusion.png")
        status_rows.append({"figure": "fig09_confusion.png", "status": "illustrative"})
        return
    frame = pd.read_csv(path)
    matrix = pd.DataFrame(0, index=keys, columns=list(DISPLAY_NAMES) + ["missed"])
    for _, row in frame.iterrows():
        gt = row["gt_class"] if row["gt_class"] in DISPLAY_NAMES else None
        pred = row["pred_class"] if row["pred_class"] in DISPLAY_NAMES or row["pred_class"] == "missed" else None
        if gt is None or pred is None:
            continue
        matrix.loc[gt, pred] += 1
    image = ax.imshow(matrix.values, cmap=CMAP, aspect="auto")
    ax.set_xticks(range(matrix.shape[1]))
    ax.set_yticks(range(matrix.shape[0]))
    ax.set_xticklabels([DISPLAY_NAMES.get(c, c) for c in matrix.columns], rotation=30, ha="right")
    ax.set_yticklabels([DISPLAY_NAMES.get(c, c) for c in matrix.index])
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(j, i, str(int(matrix.values[i, j])), ha="center", va="center", fontsize=8)
    ax.set_xlabel("Predicted class")
    ax.set_ylabel("Ground-truth class")
    ax.set_title("Baseline class consistency, including misses")
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04, label="Count")
    fig.text(0.01, 0.01, "Source: results/baseline_confusion_long.csv. Matches ignore class, then record the predicted label.", fontsize=8)
    save(fig, "fig09_confusion.png")
    status_rows.append({"figure": "fig09_confusion.png", "status": "measured"})


def risk_heatmap(status_rows: list[dict]):
    path = RESULTS / "risk_register.csv"
    fig, ax = plt.subplots(figsize=(7.2, 6.0))
    grid = np.array([[i * j for j in range(1, 6)] for i in range(1, 6)], dtype=float)
    ax.imshow(grid, cmap=RISK_CMAP, origin="lower", vmin=1, vmax=25)
    ax.set_xticks(range(5))
    ax.set_yticks(range(5))
    ax.set_xticklabels([1, 2, 3, 4, 5])
    ax.set_yticklabels([1, 2, 3, 4, 5])
    ax.set_xlabel("Impact (1 = negligible, 5 = severe)")
    ax.set_ylabel("Likelihood (1 = rare, 5 = almost certain)")
    ax.set_title("Likelihood-impact scores for the audit risk register")
    if not path.exists():
        banner(ax, "ILLUSTRATIVE EXAMPLE ONLY\nRisk register was not generated")
        save(fig, "fig10_risk_heatmap.png")
        status_rows.append({"figure": "fig10_risk_heatmap.png", "status": "illustrative"})
        return
    frame = pd.read_csv(path)
    grouped: dict[tuple[int, int], list[str]] = {}
    for _, row in frame.iterrows():
        key = (int(row["impact"]) - 1, int(row["likelihood"]) - 1)
        grouped.setdefault(key, []).append(str(row["risk_id"]))
    for (x_pos, y_pos), labels in grouped.items():
        ax.text(
            x_pos,
            y_pos,
            "\n".join(labels),
            ha="center",
            va="center",
            fontsize=8,
            color=NAVY,
            fontweight="bold",
        )
    fig.text(0.01, 0.01, "Source: results/risk_register.csv. Score = likelihood × impact. IDs are defined in that file.", fontsize=8)
    save(fig, "fig10_risk_heatmap.png")
    status_rows.append({"figure": "fig10_risk_heatmap.png", "status": "measured"})


def control_coverage(status_rows: list[dict]):
    path = TABLES / "control_coverage.csv"
    fig, ax = plt.subplots(figsize=(9.0, 5.2))
    if not path.exists():
        ax.set_title("Control coverage")
        banner(ax, "ILLUSTRATIVE EXAMPLE ONLY")
        save(fig, "fig12_control_coverage.png")
        status_rows.append({"figure": "fig12_control_coverage.png", "status": "illustrative"})
        return
    frame = pd.read_csv(path)
    controls = [c for c in frame.columns if c != "risk_id"]
    image = ax.imshow(frame[controls].values, cmap=CMAP, vmin=0, vmax=1, aspect="auto")
    ax.set_yticks(range(len(frame)))
    ax.set_yticklabels(frame["risk_id"].tolist(), fontsize=8)
    ax.set_xticks(range(len(controls)))
    ax.set_xticklabels([c.replace("_", "\n") for c in controls], fontsize=7)
    ax.set_title("Which controls address which risks")
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04, label="Addressed (1) or not the primary control (0)")
    fig.text(0.01, 0.01, "Source: tables/control_coverage.csv. A mark means the control is relevant. It does not mean the risk is eliminated.", fontsize=8)
    save(fig, "fig12_control_coverage.png")
    status_rows.append({"figure": "fig12_control_coverage.png", "status": "measured"})


def atlas_table_figure(status_rows: list[dict]):
    path = RESEARCH_ATLAS if False else None
    from config import RESEARCH

    csv_path = RESEARCH / "atlas_mapping.csv"
    fig, ax = plt.subplots(figsize=(11.5, 4.8))
    ax.axis("off")
    ax.set_title("MITRE ATLAS techniques considered in this audit", loc="left")
    if not csv_path.exists():
        banner(ax, "ILLUSTRATIVE EXAMPLE ONLY")
        save(fig, "fig11_atlas_mapping.png")
        status_rows.append({"figure": "fig11_atlas_mapping.png", "status": "illustrative"})
        return
    short_evidence = {
        "AML.T0043": "Laboratory sensitivity test",
        "AML.T0015": "Plausible consequence of measured misses",
        "AML.T0041": "Literature and scenario; not physical",
        "AML.T0040": "Scenario, not a networked test",
        "AML.T0042": "Offline verification by the evaluators",
        "AML.T0044": "Scenario, weights were not stolen",
        "AML.T0018": "Scenario, weights were not edited",
        "AML.T0020": "Scenario, training data were not poisoned",
        "AML.T0059": "Scenario, labels were not corrupted",
        "AML.T0031": "Plausible if degradation is unmonitored",
        "AML.T0010": "Scenario, upstream file was not swapped",
    }
    frame = pd.read_csv(csv_path)[
        ["technique_id", "technique_name", "tactic", "evidence_type"]
    ].copy()
    frame["evidence_type"] = frame["technique_id"].map(short_evidence).fillna(frame["evidence_type"])
    table = ax.table(
        cellText=frame.values,
        colLabels=["ID", "Technique", "Tactic", "Evidence type"],
        loc="center",
        cellLoc="left",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.35)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#D5DDD8")
        if row == 0:
            cell.set_facecolor(NAVY)
            cell.set_text_props(color="white", fontweight="bold")
        elif row % 2 == 0:
            cell.set_facecolor("#F4F7F5")
    save(fig, "fig11_atlas_mapping.png")
    status_rows.append({"figure": "fig11_atlas_mapping.png", "status": "source_mapped"})


def export_examples():
    import shutil

    from config import PERTURBED, YOLO_DIR

    out = FIGURES / "examples"
    out.mkdir(parents=True, exist_ok=True)
    images = sorted((YOLO_DIR / "images" / "test").glob("*.jpg"))
    if not images:
        return
    chosen = images[0]
    shutil.copy2(chosen, out / f"original_{chosen.name}")
    for family, level in (
        ("gaussian_blur", "level3"),
        ("brightness", "level3"),
        ("localized_occlusion", "level2"),
        ("jpeg", "level3"),
    ):
        candidate = PERTURBED / family / level / "images" / chosen.name
        if candidate.exists():
            shutil.copy2(candidate, out / f"{family}_{level}_{chosen.name}")


def main() -> int:
    style()
    status_rows: list[dict] = []
    class_distribution(status_rows)
    baseline_chart(status_rows)
    line_chart(
        "recall",
        "Recall",
        "Recall versus perturbation intensity level",
        "fig03_recall_vs_intensity.png",
        status_rows,
    )
    line_chart(
        "false_negative_rate",
        "False-negative rate",
        "False-negative rate versus perturbation intensity level",
        "fig04_fnr_vs_intensity.png",
        status_rows,
    )
    map_bars(status_rows)
    line_chart(
        "mean_confidence_including_misses",
        "Mean confidence, misses scored as 0",
        "Detection confidence versus perturbation intensity",
        "fig06_confidence_degradation.png",
        status_rows,
    )
    line_chart(
        "mean_iou_including_misses",
        "Mean IoU, misses scored as 0",
        "Localization IoU versus perturbation intensity",
        "fig07_iou_degradation.png",
        status_rows,
    )
    heatmap(status_rows)
    confusion(status_rows)
    risk_heatmap(status_rows)
    atlas_table_figure(status_rows)
    control_coverage(status_rows)
    export_examples()
    pd.DataFrame(status_rows).to_csv(FIGURES / "figure_status.csv", index=False)
    print(pd.DataFrame(status_rows).to_string(index=False))
    return 0


if __name__ == "__main__":
    from config import RESEARCH as RESEARCH_ATLAS  # noqa: F401

    raise SystemExit(main())
