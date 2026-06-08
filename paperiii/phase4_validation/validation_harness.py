"""
Validation Harness — Phase 5 deliverable for Paper III.

Compares an HVEA-enhanced SIFTING acquisition run (Phase 3 output) against a
full-disk baseline image (ground truth) along the eight metrics defined in
the experimental design document:

  From Cihan's Phase 5:
    - acquisition_speed   (wall-clock seconds)
    - storage_reduction   (partial / full size ratio)
    - artifact_preservation (HVEA-targeted artifacts present in partial,
                             as a fraction of those present in baseline)

  From Paper I:
    - completeness     (HVEA-prioritized artifact classes represented)
    - integrity        (SHA-256 of acquired regions matches baseline)
    - transparency     (every decision recorded in the trace)
    - explainability   (every acquired artifact has a human-readable
                        justification grounded in the dependency graph)
    - defensibility    (qualitative score against a pre-registered rubric;
                        rubric path is configurable, defaults to a stub
                        until the rubric is locked with the advisor)

Output: a single validation report JSON with per-metric results, plus an
overall summary suitable for inclusion as a Phase 5 results table.

Usage:
    python validation_harness.py \
        --run-dir runs/charlie_nov_hvea/ \
        --baseline-image charlie_nov.E01 \
        --baseline-mount /mnt/charlie_nov_full \
        --baseline-inventory charlie_nov_baseline.dfxml \
        --out validation_report.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from collections import defaultdict
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("hvea.phase5")

CHUNK = 1024 * 1024


@dataclass
class MetricResult:
    metric: str
    source: str
    value: float | str | None
    units: str
    detail: dict[str, Any] = field(default_factory=dict)
    pass_fail: str = "n/a"   # 'pass', 'fail', 'partial', 'n/a'


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            block = fh.read(CHUNK)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_run(run_dir: Path) -> dict[str, Any]:
    """Read defensibility report + acquisition trace + reasoning trace."""
    report = json.loads((run_dir / "defensibility_report.json").read_text())
    trace_path = run_dir / "acquisition_trace.jsonl"
    trace = [json.loads(l) for l in trace_path.read_text().splitlines() if l.strip()]
    profile = json.loads((run_dir / "acquisition_profile.json").read_text())
    return {"report": report, "trace": trace, "profile": profile, "run_dir": run_dir}


def load_inventory_paths(inventory: Path) -> set[str]:
    """
    Return the set of paths present in a baseline DFXML or JSONL inventory.
    Used by completeness and artifact_preservation metrics.
    """
    suffix = inventory.suffix.lower()
    if suffix in {".jsonl", ".ndjson"}:
        paths = set()
        for line in inventory.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            paths.add(d["path"])
        return paths

    import xml.etree.ElementTree as ET
    tree = ET.parse(inventory)
    paths = set()
    for fo in tree.getroot().iter():
        tag = fo.tag.split("}")[-1] if "}" in fo.tag else fo.tag
        if tag != "fileobject":
            continue
        for child in fo:
            ctag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if ctag == "filename" and child.text:
                norm = child.text.replace("\\", "/")
                if not norm.startswith("/"):
                    norm = "/" + norm
                paths.add(norm)
                break
    return paths


# ---------------------------------------------------------------------------
# Individual metrics
# ---------------------------------------------------------------------------

def metric_acquisition_speed(run: dict[str, Any]) -> MetricResult:
    duration = run["report"]["manifest"]["duration_seconds"]
    return MetricResult(
        metric="acquisition_speed",
        source="Cihan, Phase 5",
        value=duration,
        units="seconds",
        detail={
            "started_at":  run["report"]["manifest"]["started_at"],
            "finished_at": run["report"]["manifest"]["finished_at"],
        },
    )


def metric_storage_reduction(
    run: dict[str, Any], baseline_image: Path,
) -> MetricResult:
    partial_size = run["report"]["manifest"]["counters"]["bytes_acquired"]
    baseline_size = baseline_image.stat().st_size if baseline_image.exists() else 0
    ratio = (partial_size / baseline_size) if baseline_size else 0
    return MetricResult(
        metric="storage_reduction",
        source="Cihan, Phase 5",
        value=round(ratio, 6),
        units="ratio (partial/baseline)",
        detail={
            "partial_bytes":  partial_size,
            "baseline_bytes": baseline_size,
            "reduction_percent": round((1 - ratio) * 100, 2) if baseline_size else None,
        },
    )


def metric_artifact_preservation(
    run: dict[str, Any], baseline_paths: set[str],
) -> MetricResult:
    """
    Of the HVEA-targeted artifacts that exist in the baseline, what fraction
    did the partial-image acquisition actually capture?
    """
    profile_targets = set()
    for g in run["profile"]["groups"]:
        for c in g["criteria"]:
            profile_targets.add(c["source_path"])

    targets_in_baseline = {p for p in profile_targets if p in baseline_paths}
    acquired_paths = {
        # Trace stores paths relative to mount; profile source_paths are
        # absolute-ish. We normalize to leading slash for comparison.
        ("/" + r["source_path"].lstrip("/"))
        for r in run["trace"] if r["decision"] == "acquired"
    }
    acquired_in_baseline = {p for p in targets_in_baseline if p in acquired_paths}

    n = len(targets_in_baseline)
    captured = len(acquired_in_baseline)
    fraction = (captured / n) if n else 1.0

    return MetricResult(
        metric="artifact_preservation",
        source="Cihan, Phase 5",
        value=round(fraction, 6),
        units="fraction",
        detail={
            "hvea_targets_in_baseline": n,
            "acquired": captured,
            "missing": sorted(targets_in_baseline - acquired_in_baseline)[:20],
        },
        pass_fail="pass" if fraction >= 0.95 else ("partial" if fraction >= 0.80 else "fail"),
    )


def metric_completeness(run: dict[str, Any]) -> MetricResult:
    """Whether every HVEA-prioritized artifact class (layer) is represented."""
    profile_layers = set()
    for g in run["profile"]["groups"]:
        for c in g["criteria"]:
            profile_layers.update(c["hvea_layers"])

    represented = set()
    for r in run["trace"]:
        if r["decision"] == "acquired":
            represented.update(r["hvea_layers"])

    missing = sorted(profile_layers - represented)
    return MetricResult(
        metric="completeness",
        source="Paper I",
        value=round(len(represented) / len(profile_layers), 4) if profile_layers else 1.0,
        units="fraction of layers represented",
        detail={
            "layers_targeted":   sorted(profile_layers),
            "layers_represented": sorted(represented),
            "missing": missing,
        },
        pass_fail="pass" if not missing else "fail",
    )


def metric_integrity(
    run: dict[str, Any], baseline_mount: Path,
) -> MetricResult:
    """
    For each acquired file, verify that SHA-256 of the acquired copy matches
    SHA-256 of the corresponding file in the baseline mount.
    """
    mismatches: list[dict[str, str]] = []
    checked = 0
    matched = 0

    run_dir = run["run_dir"]
    for r in run["trace"]:
        if r["decision"] != "acquired" or not r.get("output_path"):
            continue
        acquired_path = run_dir / r["output_path"]
        baseline_path = baseline_mount / r["source_path"].lstrip("/").replace("\\", "/")
        if not baseline_path.exists() or not acquired_path.exists():
            continue
        checked += 1
        acquired_sha = r.get("sha256") or sha256_file(acquired_path)
        baseline_sha = sha256_file(baseline_path)
        if acquired_sha == baseline_sha:
            matched += 1
        else:
            mismatches.append({
                "path": r["source_path"],
                "acquired_sha": acquired_sha,
                "baseline_sha": baseline_sha,
            })

    return MetricResult(
        metric="integrity",
        source="Paper I",
        value=round(matched / checked, 6) if checked else 1.0,
        units="fraction of acquired files hash-matching baseline",
        detail={"checked": checked, "matched": matched, "mismatches": mismatches[:10]},
        pass_fail="pass" if not mismatches else "fail",
    )


def metric_transparency(run: dict[str, Any]) -> MetricResult:
    """Every decision recorded? Compare profile criteria count against trace records."""
    expected_decisions = sum(len(g["criteria"]) for g in run["profile"]["groups"])
    recorded = len(run["trace"])
    covered = (recorded >= expected_decisions)
    return MetricResult(
        metric="transparency",
        source="Paper I",
        value="full" if covered else "partial",
        units="decision coverage",
        detail={"expected": expected_decisions, "recorded": recorded},
        pass_fail="pass" if covered else "fail",
    )


def metric_explainability(run: dict[str, Any]) -> MetricResult:
    """Every acquired artifact has a rationale grounded in HVEA?"""
    missing: list[str] = []
    acquired = 0
    explained = 0
    for r in run["trace"]:
        if r["decision"] != "acquired":
            continue
        acquired += 1
        rationale = r.get("rationale", "")
        # Heuristic: the rationale must reference Tier or Layer.
        if "Tier" in rationale or "Layer" in rationale:
            explained += 1
        else:
            missing.append(r.get("source_path", ""))
    return MetricResult(
        metric="explainability",
        source="Paper I + Phase 4",
        value=round(explained / acquired, 6) if acquired else 1.0,
        units="fraction of acquired artifacts with HVEA-grounded rationale",
        detail={"acquired": acquired, "explained": explained, "missing_first_10": missing[:10]},
        pass_fail="pass" if not missing else "fail",
    )


def metric_defensibility(
    run: dict[str, Any], rubric_path: Path | None,
) -> MetricResult:
    """
    Qualitative scoring against a pre-registered rubric. Until the rubric is
    locked with the advisor, this returns a structured placeholder so that
    the validation report still surfaces the metric and the open question.
    """
    if rubric_path is None or not rubric_path.exists():
        return MetricResult(
            metric="defensibility",
            source="Paper I",
            value=None,
            units="rubric score",
            detail={
                "status": "rubric_not_yet_locked",
                "note": (
                    "Pre-registered scoring rubric for chain-of-custody, "
                    "reproducibility, and soundness of dependency reasoning "
                    "is an open question for the advisor (see experimental "
                    "design doc, section 7)."
                ),
            },
            pass_fail="n/a",
        )

    # When the rubric exists, score against it. This block is a stub that
    # tallies the rubric's declared dimensions and returns mean + per-dimension.
    rubric = json.loads(rubric_path.read_text())
    scores = {d["name"]: d.get("score", 0) for d in rubric.get("dimensions", [])}
    mean = sum(scores.values()) / len(scores) if scores else 0
    return MetricResult(
        metric="defensibility",
        source="Paper I",
        value=round(mean, 4),
        units="rubric mean (0-5)",
        detail={"per_dimension": scores, "rubric_path": str(rubric_path)},
        pass_fail="pass" if mean >= 4.0 else "partial" if mean >= 3.0 else "fail",
    )


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def validate(
    run_dir: Path,
    baseline_image: Path | None,
    baseline_mount: Path | None,
    baseline_inventory: Path | None,
    rubric_path: Path | None,
) -> dict[str, Any]:
    run = load_run(run_dir)
    metrics: list[MetricResult] = []

    metrics.append(metric_acquisition_speed(run))
    if baseline_image:
        metrics.append(metric_storage_reduction(run, baseline_image))
    if baseline_inventory:
        baseline_paths = load_inventory_paths(baseline_inventory)
        metrics.append(metric_artifact_preservation(run, baseline_paths))
    metrics.append(metric_completeness(run))
    if baseline_mount:
        metrics.append(metric_integrity(run, baseline_mount))
    metrics.append(metric_transparency(run))
    metrics.append(metric_explainability(run))
    metrics.append(metric_defensibility(run, rubric_path))

    return {
        "report_type": "validation_report",
        "schema_version": "1.0.0",
        "run_dir": str(run_dir),
        "baseline": {
            "image": str(baseline_image) if baseline_image else None,
            "mount": str(baseline_mount) if baseline_mount else None,
            "inventory": str(baseline_inventory) if baseline_inventory else None,
        },
        "metrics": [asdict(m) for m in metrics],
        "summary": {
            m.metric: {"value": m.value, "units": m.units, "pass_fail": m.pass_fail}
            for m in metrics
        },
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--run-dir", required=True, type=Path)
    p.add_argument("--baseline-image",     type=Path, default=None)
    p.add_argument("--baseline-mount",     type=Path, default=None)
    p.add_argument("--baseline-inventory", type=Path, default=None)
    p.add_argument("--rubric", type=Path, default=None)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    report = validate(
        args.run_dir,
        args.baseline_image,
        args.baseline_mount,
        args.baseline_inventory,
        args.rubric,
    )
    args.out.write_text(json.dumps(report, indent=2))

    summary = report["summary"]
    logger.info("Validation complete. Output: %s", args.out)
    for m_name, m_val in summary.items():
        logger.info("  %-24s %s (%s) [%s]",
                    m_name, m_val["value"], m_val["units"], m_val["pass_fail"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
