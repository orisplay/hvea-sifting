"""
HVEA-Enhanced SIFTING Acquisition Harness — Phase 3 deliverable for Paper III.

Executes a SIFTING-compatible acquisition profile (Phase 2 output) against a
mounted disk image, producing:

  1. A partial image directory containing the acquired files, organized by
     HVEA layer for traceability.
  2. A reasoning trace recording every per-criterion decision (acquired,
     skipped, failed) with the HVEA grounding inherited from Phase 1.
  3. A defensibility report packaging the run manifest, environment, hashes,
     and the reasoning trace as a single auditable artifact (Phase 4 hook).

Acquisition policy: dependency-respecting single pass. Groups execute in
tier order I → II → III → IV. Within a group, criteria execute in
sequence number order. No group starts until all its declared
dependency-context layers have completed in earlier groups.

The harness deliberately treats the mounted image as a read-only file tree.
That decoupling lets the same harness drive multiple real acquisition
mechanisms in Phase 5 (sifting-style file extraction, raw-sector
acquisition, etc.) without changing the reasoning above.

Usage:
    python acquisition_harness.py --profile sifting_profile.json \
                                  --mount  /mnt/image_ro \
                                  --out    runs/charlie_nov_hvea/ \
                                  --image-name charlie_nov.E01 \
                                  --image-hash <sha256>
"""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import json
import logging
import platform
import re
import shutil
import sys
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("hvea.phase3")

CHUNK = 1024 * 1024  # 1 MiB


# ---------------------------------------------------------------------------
# Pattern matching against the mount tree
# ---------------------------------------------------------------------------

def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Mirror the Phase 1 glob dialect for consistent matching."""
    out = ["^"]
    i = 0
    while i < len(pattern):
        if pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    out.append("$")
    return re.compile("".join(out), re.IGNORECASE)


def _resolve_source(mount: Path, source_path: str) -> Path | None:
    """
    Resolve a logical source_path (as recorded in the profile) to a concrete
    file on the read-only mount. Returns None if the file is missing or if the
    path attempts to escape the mount boundary.

    Defense in depth: even though Phase 1 now filters '.'/'..' inventory
    entries, the harness independently refuses any source_path containing a
    traversal component, and verifies the final resolved path stays within
    the mount. This prevents a malformed profile from acquiring the whole
    disk via '/RECYCLER/..' -> partition root.
    """
    rel = source_path.lstrip("/").replace("\\", "/")

    # Reject any traversal component outright.
    parts = [p for p in rel.split("/") if p != ""]
    if any(p in (".", "..") for p in parts):
        return None

    candidate = mount / rel
    if candidate.exists():
        resolved = candidate.resolve()
        mount_resolved = mount.resolve()
        # Confirm the resolved path is inside the mount.
        if not str(resolved).startswith(str(mount_resolved)):
            return None
        return candidate

    # Case-insensitive fallback — Windows filesystems mount case-preserving
    # on Linux but the inventory may have a different case than disk.
    parent = mount
    for part in parts:
        if not parent.exists():
            return None
        match = None
        for entry in parent.iterdir():
            if entry.name.lower() == part.lower():
                match = entry
                break
        if match is None:
            return None
        parent = match
    if not parent.exists():
        return None
    # Boundary check on the resolved fallback path too.
    if not str(parent.resolve()).startswith(str(mount.resolve())):
        return None
    return parent


# ---------------------------------------------------------------------------
# Hashing and copying
# ---------------------------------------------------------------------------

def sha256_file(path: Path) -> tuple[str, int]:
    h = hashlib.sha256()
    n = 0
    with path.open("rb") as fh:
        while True:
            block = fh.read(CHUNK)
            if not block:
                break
            h.update(block)
            n += len(block)
    return h.hexdigest(), n


def copy_with_hash(src: Path, dst: Path) -> tuple[str, int]:
    """Stream-copy a file and compute SHA-256 in the same pass."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256()
    n = 0
    with src.open("rb") as fin, dst.open("wb") as fout:
        while True:
            block = fin.read(CHUNK)
            if not block:
                break
            fout.write(block)
            h.update(block)
            n += len(block)
    return h.hexdigest(), n


# ---------------------------------------------------------------------------
# Trace record
# ---------------------------------------------------------------------------

@dataclass
class AcquisitionRecord:
    source_path: str
    decision: str            # acquired | skipped_not_found | skipped_policy | failed
    hvea_layers: list[str]
    hvea_tiers: list[int]
    primary_layer: str
    sequence: int
    group_id: str
    output_path: str | None = None
    bytes_acquired: int = 0
    sha256: str | None = None
    error: str | None = None
    rationale: str = ""


@dataclass
class RunManifest:
    image_name: str
    image_hash: str
    profile_name: str
    profile_version: str
    started_at: str
    finished_at: str
    duration_seconds: float
    tool: dict[str, str]
    counters: dict[str, int]


# ---------------------------------------------------------------------------
# Acquisition core
# ---------------------------------------------------------------------------

def acquire_profile(
    profile: dict[str, Any],
    mount: Path,
    out_dir: Path,
) -> tuple[RunManifest, list[AcquisitionRecord]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    started_at = time.time()

    trace: list[AcquisitionRecord] = []
    counters = {
        "acquired": 0,
        "also_acquired_dedup": 0,
        "skipped_not_found": 0,
        "skipped_policy": 0,
        "failed": 0,
        "bytes_acquired": 0,
    }

    # Dedup: a single physical file may match multiple HVEA layers (e.g. a
    # document in a Temp dir matched by both Layer C payload and Layer G
    # residue patterns). We acquire the bytes ONCE, keyed by the file's
    # mount-relative path, and record subsequent matches as 'also_acquired'
    # for cross-layer explainability without duplicating storage.
    acquired_paths: dict[str, str] = {}  # mount-relative source -> output_path

    # Iterate groups in tier order; within each group, criteria are already
    # sequence-ordered by the Phase 2 mapper.
    for group in profile["groups"]:
        group_id = group["group_id"]
        logger.info(
            "Begin group %s (Tier %s, %s) — %d criteria",
            group_id, group["tier_roman"], group["tier_name"],
            len(group["criteria"]),
        )

        for criterion in group["criteria"]:
            source_path = criterion["source_path"]
            seq = criterion["sequence"]
            primary_layer = criterion["primary_layer"]

            src = _resolve_source(mount, source_path)
            if src is None:
                trace.append(AcquisitionRecord(
                    source_path=source_path,
                    decision="skipped_not_found",
                    hvea_layers=criterion["hvea_layers"],
                    hvea_tiers=criterion["hvea_tiers"],
                    primary_layer=primary_layer,
                    sequence=seq,
                    group_id=group_id,
                    rationale=(
                        "Path declared in HVEA profile but not present on this "
                        "image. Expected on Windows systems; recorded for "
                        "completeness analysis."
                    ),
                ))
                counters["skipped_not_found"] += 1
                continue

            if not src.is_file():
                # Directory pattern — expand it.
                # For now we acquire all regular files under the directory.
                expanded = [p for p in src.rglob("*") if p.is_file()]
                if not expanded:
                    trace.append(AcquisitionRecord(
                        source_path=source_path,
                        decision="skipped_not_found",
                        hvea_layers=criterion["hvea_layers"],
                        hvea_tiers=criterion["hvea_tiers"],
                        primary_layer=primary_layer,
                        sequence=seq,
                        group_id=group_id,
                        rationale="Directory exists but is empty.",
                    ))
                    counters["skipped_not_found"] += 1
                    continue
                files = expanded
            else:
                files = [src]

            for fpath in files:
                # Mount-relative key for dedup.
                try:
                    mount_rel = str(fpath.relative_to(mount))
                except ValueError:
                    mount_rel = str(fpath)

                # Already acquired by an earlier criterion/layer? Record the
                # cross-layer relevance but do not recopy the bytes.
                if mount_rel in acquired_paths:
                    trace.append(AcquisitionRecord(
                        source_path=mount_rel,
                        decision="also_acquired",
                        hvea_layers=criterion["hvea_layers"],
                        hvea_tiers=criterion["hvea_tiers"],
                        primary_layer=primary_layer,
                        sequence=seq,
                        group_id=group_id,
                        output_path=acquired_paths[mount_rel],
                        bytes_acquired=0,
                        sha256=None,
                        rationale=(
                            "Already acquired by an earlier layer/criterion; "
                            "recorded as additional layer-of-relevance for "
                            "cross-layer explainability. Bytes not duplicated. "
                            + criterion["rationale"]
                        ),
                    ))
                    counters["also_acquired_dedup"] += 1
                    continue

                rel_under_source = fpath.relative_to(src) if src.is_dir() else fpath.name
                # Layout: out_dir / partial_image / tier_X / <primary_layer> / <original_path>
                if src.is_dir():
                    dst = out_dir / "partial_image" / group_id / primary_layer / source_path.lstrip("/") / rel_under_source
                else:
                    # Preserve original path under the partial_image root.
                    dst = out_dir / "partial_image" / group_id / primary_layer / source_path.lstrip("/")

                try:
                    sha, nbytes = copy_with_hash(fpath, dst)
                    acquired_paths[mount_rel] = str(dst.relative_to(out_dir))
                    trace.append(AcquisitionRecord(
                        source_path=mount_rel,
                        decision="acquired",
                        hvea_layers=criterion["hvea_layers"],
                        hvea_tiers=criterion["hvea_tiers"],
                        primary_layer=primary_layer,
                        sequence=seq,
                        group_id=group_id,
                        output_path=str(dst.relative_to(out_dir)),
                        bytes_acquired=nbytes,
                        sha256=sha,
                        rationale=criterion["rationale"],
                    ))
                    counters["acquired"] += 1
                    counters["bytes_acquired"] += nbytes
                except Exception as e:
                    trace.append(AcquisitionRecord(
                        source_path=str(fpath),
                        decision="failed",
                        hvea_layers=criterion["hvea_layers"],
                        hvea_tiers=criterion["hvea_tiers"],
                        primary_layer=primary_layer,
                        sequence=seq,
                        group_id=group_id,
                        error=f"{type(e).__name__}: {e}",
                        rationale=criterion["rationale"],
                    ))
                    counters["failed"] += 1

    finished_at = time.time()
    manifest = RunManifest(
        image_name="",  # filled by caller
        image_hash="",
        profile_name=profile.get("profile_name", "unknown"),
        profile_version=profile.get("version", "unknown"),
        started_at=dt.datetime.fromtimestamp(started_at, dt.timezone.utc).isoformat(),
        finished_at=dt.datetime.fromtimestamp(finished_at, dt.timezone.utc).isoformat(),
        duration_seconds=round(finished_at - started_at, 3),
        tool={
            "name": "hvea_acquisition_harness",
            "version": "1.0.0",
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        counters=counters,
    )
    return manifest, trace


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def write_trace(trace: list[AcquisitionRecord], path: Path) -> None:
    with path.open("w") as fh:
        for r in trace:
            fh.write(json.dumps(asdict(r)) + "\n")


def write_defensibility_report(
    manifest: RunManifest, trace_path: Path, profile_path: Path,
    out_path: Path,
) -> None:
    """
    Bundle the run manifest, environment, and pointers to the reasoning trace
    and profile into a single auditable JSON document. This is the Phase 4
    hook: every acquisition produces one of these, automatically, not
    retrofitted.
    """
    report = {
        "report_type": "defensibility_report",
        "schema_version": "1.0.0",
        "manifest": asdict(manifest),
        "artifacts": {
            "reasoning_trace": str(trace_path.name),
            "acquisition_profile": str(profile_path.name),
        },
        "chain_of_custody": {
            "image_name": manifest.image_name,
            "image_hash": manifest.image_hash,
            "acquisition_started_at": manifest.started_at,
            "acquisition_finished_at": manifest.finished_at,
            "operator": "to_be_filled_by_examiner",
            "tool_attestation": manifest.tool,
        },
        "summary": manifest.counters,
    }
    out_path.write_text(json.dumps(report, indent=2))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--profile", required=True, type=Path)
    p.add_argument("--mount",   required=True, type=Path,
                   help="Path to the read-only mounted image root.")
    p.add_argument("--out",     required=True, type=Path,
                   help="Output run directory (created if absent).")
    p.add_argument("--image-name", required=True)
    p.add_argument("--image-hash", required=True,
                   help="SHA-256 of the source image. Treat as evidence integrity anchor.")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    profile = json.loads(args.profile.read_text())
    manifest, trace = acquire_profile(profile, args.mount, args.out)
    manifest.image_name = args.image_name
    manifest.image_hash = args.image_hash

    trace_path = args.out / "acquisition_trace.jsonl"
    write_trace(trace, trace_path)

    profile_copy = args.out / "acquisition_profile.json"
    shutil.copyfile(args.profile, profile_copy)

    report_path = args.out / "defensibility_report.json"
    write_defensibility_report(manifest, trace_path, profile_copy, report_path)

    logger.info(
        "Acquisition complete: %d acquired (%.2f MB), %d not_found, %d failed. "
        "Duration: %.2fs. Output: %s",
        manifest.counters["acquired"],
        manifest.counters["bytes_acquired"] / (1024 * 1024),
        manifest.counters["skipped_not_found"],
        manifest.counters["failed"],
        manifest.duration_seconds,
        args.out,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
