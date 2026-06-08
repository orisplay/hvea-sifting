"""
HVEA-to-SIFTING Profile Mapper — Phase 2 deliverable for Paper III.

Consumes the Phase 1 output (acquisition target list + reasoning trace) and
produces an acquisition profile in the form SIFTING expects: ordered groups
of selection criteria together with metadata that drives the Phase 3
acquisition mechanism.

This module is the bridge between HVEA reasoning ('what to acquire, in what
order') and SIFTING execution ('how to acquire it from disk').

Output format is deliberately a superset of what a vanilla SIFTING profile
contains, so a SIFTING-compatible mechanism can read the criteria fields
while the additional HVEA-grounding fields (layer, tier, dependency context)
remain available for the explainability metric.

Usage:
    python sifting_profile_mapper.py --targets targets.json \
                                     --graph hvea_graph.json \
                                     --out sifting_profile.json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import defaultdict
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("hvea.phase2")


@dataclass
class AcquisitionGroup:
    """A sifting-style acquisition group.

    Groups are ordered by HVEA tier (lowest tier first). Within a group,
    criteria are ordered by sequence number from Phase 1.
    """
    group_id: str
    tier: int
    tier_roman: str
    tier_name: str
    layers: list[str]
    sequence_range: tuple[int, int]
    criteria: list[dict[str, Any]] = field(default_factory=list)
    dependency_context: list[str] = field(default_factory=list)


def map_targets_to_profile(
    targets: list[dict[str, Any]],
    graph: dict[str, Any],
) -> dict[str, Any]:
    """
    Translate HVEA acquisition targets into a SIFTING-compatible profile.

    Grouping strategy:
      - Group by primary_tier (Roman I through IV).
      - Within a group, list criteria in Phase 1 sequence order.
      - Carry the dependency context (which earlier tiers must complete first)
        on the group itself, so the acquisition mechanism can enforce ordering.

    The 'criteria' field is what a SIFTING-style mechanism actually consumes:
    one entry per artifact-to-acquire, with the source path, scope, and a
    pointer back to the HVEA layer(s) the artifact serves.
    """
    tiers = {t["id"]: t for t in graph["tiers"]}
    layers = {l["id"]: l for l in graph["layers"]}

    # Bucket targets by primary_tier preserving sequence order.
    by_tier: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for t in targets:
        by_tier[t["primary_tier"]].append(t)
    for tier_id in by_tier:
        by_tier[tier_id].sort(key=lambda x: x["sequence"])

    groups: list[AcquisitionGroup] = []
    for tier_id in sorted(by_tier):
        tier_meta = tiers[tier_id]
        items = by_tier[tier_id]
        layer_ids_in_group = sorted({t["primary_layer"] for t in items})

        # Compute which earlier-tier layers this group depends on.
        # Cross-tier dependencies are inherited from any layer in this group.
        dep_ctx: set[str] = set()
        for t in items:
            for dep in t.get("dependencies_satisfied", []):
                if layers[dep]["tier"] < tier_id:
                    dep_ctx.add(dep)

        group = AcquisitionGroup(
            group_id=f"tier_{tier_meta['roman']}",
            tier=tier_id,
            tier_roman=tier_meta["roman"],
            tier_name=tier_meta["name"],
            layers=layer_ids_in_group,
            sequence_range=(items[0]["sequence"], items[-1]["sequence"]),
            dependency_context=sorted(dep_ctx),
            criteria=[
                {
                    "source_path": t["inventory_path"],
                    "patterns": t["matched_patterns"],
                    "scope": "file_or_path",
                    "hvea_layers": t["layers"],
                    "hvea_tiers": t["tiers"],
                    "primary_layer": t["primary_layer"],
                    "sequence": t["sequence"],
                    "allocated_only": t["allocated_only"],
                    "rationale": t["rationale"],
                }
                for t in items
            ],
        )
        groups.append(group)

    profile = {
        "profile_name": "hvea_driven_sifting_profile",
        "version": "1.0.0",
        "source_model": graph.get("model", "HVEA"),
        "ordering_policy": "dependency_respecting_single_pass",
        "groups": [asdict(g) for g in groups],
        "totals": {
            "groups": len(groups),
            "criteria": sum(len(g.criteria) for g in groups),
        },
    }
    return profile


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Map an HVEA acquisition target list into a SIFTING-compatible "
            "acquisition profile, preserving HVEA grounding for "
            "explainability."
        )
    )
    p.add_argument("--targets", required=True, type=Path,
                   help="Phase 1 acquisition targets JSON.")
    p.add_argument("--graph", required=True, type=Path,
                   help="HVEA graph JSON (for tier metadata).")
    p.add_argument("--out", required=True, type=Path,
                   help="Output: SIFTING-compatible profile JSON.")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    targets_doc = json.loads(args.targets.read_text())
    graph_doc = json.loads(args.graph.read_text())
    targets = targets_doc["targets"]

    profile = map_targets_to_profile(targets, graph_doc)
    args.out.write_text(json.dumps(profile, indent=2))

    logger.info(
        "Wrote SIFTING profile: %d groups, %d criteria. Path: %s",
        profile["totals"]["groups"], profile["totals"]["criteria"], args.out,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
