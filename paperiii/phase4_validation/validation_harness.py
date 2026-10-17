"""
Validation Harness — Phase 4 deliverable for Paper III.

Compares an HVEA-enhanced SIFTING acquisition run (Phase 3 output) against a
full-disk baseline image (ground truth) along the eight metrics defined in
the experimental design document:

  From the Phase 4 validation design:
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
overall summary suitable for inclusion as a Phase 4 results table.

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

logger = logging.getLogger("hvea.phase4")

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
        source="Phase 4 validation",
        value=duration,
        units="seconds",
        detail={
            "started_at":  run["report"]["manifest"]["started_at"],
            "finished_at": run["report"]["manifest"]["finished_at"],
        },
    )


def _logical_media_size(baseline_image: Path, baseline_mount: Path | None) -> tuple[int, str]:
    """
    Determine the logical media size of the source — the size a full,
    uncompressed disk image would occupy — which is the correct denominator
    for a storage-reduction claim against full-disk imaging.

    Priority:
      1. ewfinfo "media size" (handles multi-segment E01s correctly; the
         compressed .E01 file size does NOT — an 18-segment image reports its
         first segment as ~1.5 GB while the media is 40 GiB).
      2. Mounted-partition size via the loop device backing the mount.
      3. Fallback: on-disk size of the image file (only correct for a
         single-segment uncompressed image; flagged as approximate).
    """
    import subprocess, shutil
    # 1. ewfinfo media size
    if shutil.which("ewfinfo"):
        try:
            out = subprocess.run(
                ["ewfinfo", str(baseline_image)],
                capture_output=True, text=True, timeout=60,
            ).stdout
            for line in out.splitlines():
                # "Media size: 40 GiB (42949672960 bytes)"
                if "media size" in line.lower() and "(" in line:
                    digits = "".join(ch for ch in line.split("(")[1] if ch.isdigit())
                    if digits:
                        return int(digits), "ewfinfo_media_size"
        except Exception:
            pass
    # 2. mounted partition size
    if baseline_mount is not None:
        try:
            src_dev = subprocess.run(
                ["findmnt", "-no", "SOURCE", str(baseline_mount)],
                capture_output=True, text=True, timeout=30,
            ).stdout.strip()
            if src_dev:
                size = subprocess.run(
                    ["blockdev", "--getsize64", src_dev],
                    capture_output=True, text=True, timeout=30,
                ).stdout.strip()
                if size.isdigit():
                    return int(size), "mounted_partition_size"
        except Exception:
            pass
    # 3. fallback — on-disk image size (approximate; wrong for multi-segment)
    if baseline_image.exists():
        return baseline_image.stat().st_size, "image_file_size_APPROX"
    return 0, "unknown"


def metric_storage_reduction(
    run: dict[str, Any], baseline_image: Path,
    baseline_mount: Path | None = None,
) -> MetricResult:
    partial_size = run["report"]["manifest"]["counters"]["bytes_acquired"]
    baseline_size, size_source = _logical_media_size(baseline_image, baseline_mount)
    ratio = (partial_size / baseline_size) if baseline_size else 0
    return MetricResult(
        metric="storage_reduction",
        source="Phase 4 validation",
        value=round(ratio, 6),
        units="ratio (partial/baseline media)",
        detail={
            "partial_bytes":  partial_size,
            "baseline_bytes": baseline_size,
            "baseline_size_source": size_source,
            "reduction_percent": round((1 - ratio) * 100, 2) if baseline_size else None,
        },
    )


def metric_artifact_preservation(
    run: dict[str, Any], baseline_paths: set[str],
    baseline_mount: Path | None = None,
) -> MetricResult:
    """
    Of the HVEA-targeted *files* that exist in the baseline, what fraction did
    the partial-image acquisition actually capture?

    Files-only denominator. Directory container entries are excluded from both
    numerator and denominator: a directory is not itself an evidentiary
    artifact, and the acquisition harness never copies a directory entry (it
    copies the files within). A target path is treated as a directory if any
    other known path is strictly nested beneath it (path-prefix test).

    Missing-file classification (requires the live mount). fiwalk reads the
    NTFS Master File Table and lists every file *entry* it finds, including
    entries whose data clusters have since been reused — "MFT ghosts." These
    appear in the baseline inventory but have no recoverable data, so the
    acquisition harness correctly finds nothing to copy. Such entries are not
    preservation failures. For every targeted file that was not acquired, we
    check the live mount and classify it:

        data_absent : listed in the MFT/DFXML but absent on the live mount
                      (a ghost; expected, not a failure)
        genuine_miss: present on the live mount but not acquired
                      (a real preservation gap — investigate)

    We report two rates: a conservative rate against all file targets, and a
    recoverable rate that excludes mount-verified data_absent ghosts. The
    ghost count is reported as a first-class reconciling quantity so the gap
    between the two rates is fully accounted for, never asserted.
    """
    profile_targets = set()
    for g in run["profile"]["groups"]:
        for c in g["criteria"]:
            profile_targets.add(c["source_path"])

    acquired_paths = {
        ("/" + r["source_path"].lstrip("/"))
        for r in run["trace"] if r["decision"] == "acquired"
    }

    universe = set(baseline_paths) | acquired_paths | profile_targets

    def _is_directory(path: str) -> bool:
        prefix = path.rstrip("/") + "/"
        for other in universe:
            if other != path and other.startswith(prefix):
                return True
        return False

    targets_in_baseline = {p for p in profile_targets if p in baseline_paths}
    file_targets = {p for p in targets_in_baseline if not _is_directory(p)}
    dir_targets_excluded = len(targets_in_baseline) - len(file_targets)

    acquired_file_targets = {p for p in file_targets if p in acquired_paths}
    missing = file_targets - acquired_file_targets

    # Classify every missing file against the live mount.
    data_absent: list[str] = []
    genuine_miss: list[str] = []
    classified = baseline_mount is not None and baseline_mount.exists()
    if classified:
        for p in missing:
            rel = p.lstrip("/").replace("\\", "/")
            on_mount = (baseline_mount / rel).exists()
            (genuine_miss if on_mount else data_absent).append(p)
    else:
        # Without a mount we cannot classify; treat all as unclassified.
        data_absent = []
        genuine_miss = []

    n = len(file_targets)
    captured = len(acquired_file_targets)
    conservative = (captured / n) if n else 1.0

    # Recoverable rate excludes mount-verified ghosts from the denominator.
    if classified:
        recoverable_denom = n - len(data_absent)
        recoverable = (captured / recoverable_denom) if recoverable_denom else 1.0
    else:
        recoverable = None

    # Pass/fail is judged on the recoverable rate when we could classify,
    # otherwise on the conservative rate.
    judged = recoverable if (classified and recoverable is not None) else conservative
    pass_fail = "pass" if judged >= 0.95 else ("partial" if judged >= 0.80 else "fail")

    detail = {
        "hvea_file_targets_in_baseline": n,
        "acquired": captured,
        "directory_targets_excluded": dir_targets_excluded,
        "missing_total": len(missing),
        "data_absent_ghosts": len(data_absent),
        "genuine_misses": len(genuine_miss),
        "classification_performed": classified,
        "recoverable_preservation": (round(recoverable, 6) if recoverable is not None else None),
        "genuine_miss_sample": sorted(genuine_miss)[:20],
        "data_absent_sample": sorted(data_absent)[:10],
    }

    return MetricResult(
        metric="artifact_preservation",
        source="Phase 4 validation",
        value=round(conservative, 6),
        units="fraction (files only; conservative)",
        detail=detail,
        pass_fail=pass_fail,
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
        metrics.append(metric_storage_reduction(run, baseline_image, baseline_mount))
    if baseline_inventory:
        baseline_paths = load_inventory_paths(baseline_inventory)
        metrics.append(metric_artifact_preservation(run, baseline_paths, baseline_mount))
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

    # Surface the artifact-preservation decomposition explicitly.
    for m in report["metrics"]:
        if m["metric"] == "artifact_preservation":
            d = m["detail"]
            if d.get("classification_performed"):
                logger.info(
                    "  preservation detail: %d file targets, %d acquired, "
                    "%d data-absent ghosts, %d genuine misses; "
                    "recoverable rate = %s",
                    d["hvea_file_targets_in_baseline"], d["acquired"],
                    d["data_absent_ghosts"], d["genuine_misses"],
                    d["recoverable_preservation"],
                )
                if d["genuine_misses"]:
                    logger.warning(
                        "  %d GENUINE misses (on mount but not acquired) — investigate: %s",
                        d["genuine_misses"], d["genuine_miss_sample"][:5],
                    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
