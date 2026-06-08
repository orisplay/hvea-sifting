"""
HVEA Reasoning Module — Phase 1 deliverable for Paper III.

Loads the formalized HVEA dependency graph (hvea_graph.json) and, given a
baseline file inventory from a disk image, produces a dependency-respecting
ordered list of acquisition targets together with a reasoning trace explaining
each acquisition decision.

This module is the input to Phase 2 (HVEA-to-SIFTING profile mapping) and the
substrate for the explainability metric in Phase 4.

Usage:
    python hvea_reasoner.py --graph hvea_graph.json \
                            --inventory baseline_inventory.dfxml \
                            --out targets.json --trace trace.jsonl

The module is deliberately mechanism-agnostic. It produces *what to acquire*
(HVEA target list); Phase 2 translates that into *how SIFTING acquires it*.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

logger = logging.getLogger("hvea")


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Layer:
    id: str
    name: str
    tier: int
    purpose: str
    core_artifacts: list[str]
    typical_sources: list[str]
    acquisition_paths: list[dict[str, Any]]


@dataclass
class Dependency:
    src: str
    dst: str
    type: str
    rationale: str
    strength: str = "strong"


@dataclass
class HveaGraph:
    """In-memory representation of the formalized HVEA graph."""
    version: str
    tiers: dict[int, dict[str, Any]]
    layers: dict[str, Layer]
    dependencies: list[Dependency]
    convergence_patterns: list[dict[str, Any]] = field(default_factory=list)

    def predecessors(self, layer_id: str) -> list[str]:
        """Layers that `layer_id` interpretively depends on."""
        return [d.src for d in self.dependencies if d.dst == layer_id]

    def successors(self, layer_id: str) -> list[str]:
        """Layers that interpretively depend on `layer_id`."""
        return [d.dst for d in self.dependencies if d.src == layer_id]

    def topological_layer_order(self) -> list[str]:
        """
        Kahn's algorithm. Returns layers in dependency order (predecessors first).
        Ties broken by tier, then alphabetically. Raises if a cycle exists.
        """
        in_degree: dict[str, int] = {lid: 0 for lid in self.layers}
        for d in self.dependencies:
            in_degree[d.dst] += 1

        # Roots: layers with no incoming dependencies.
        ready: deque[str] = deque(
            sorted(
                [lid for lid, deg in in_degree.items() if deg == 0],
                key=lambda lid: (self.layers[lid].tier, lid),
            )
        )
        order: list[str] = []

        while ready:
            lid = ready.popleft()
            order.append(lid)
            for succ in sorted(self.successors(lid),
                               key=lambda x: (self.layers[x].tier, x)):
                in_degree[succ] -= 1
                if in_degree[succ] == 0:
                    ready.append(succ)

        if len(order) != len(self.layers):
            raise ValueError(
                "HVEA graph contains a cycle. Topological order undefined. "
                f"Resolved: {order}. Unresolved: "
                f"{[k for k, v in in_degree.items() if v > 0]}"
            )
        return order


# ---------------------------------------------------------------------------
# Inventory item
# ---------------------------------------------------------------------------

@dataclass
class InventoryItem:
    """A file/object from the baseline DFXML inventory."""
    path: str
    size: int = 0
    allocated: bool = True
    inode: str | None = None


# ---------------------------------------------------------------------------
# Acquisition target produced by reasoning
# ---------------------------------------------------------------------------

@dataclass
class AcquisitionTarget:
    """One item the acquisition mechanism is being asked to collect.

    An inventory item may legitimately match more than one HVEA layer
    (e.g. the SYSTEM registry hive serves both Layer A's environment baseline
    and Layer D's network configuration). The mechanism only needs to acquire
    the bytes once, so `layers` and `tiers` are lists: the item is acquired
    once, and the trace records every layer it satisfies.
    """
    inventory_path: str
    matched_patterns: list[str]
    layers: list[str]
    tiers: list[int]
    primary_layer: str                  # first (lowest-tier) layer that claimed the item
    primary_tier: int
    sequence: int                       # global acquisition order
    rationale: str
    dependencies_satisfied: list[str]   # predecessor layers already targeted
    allocated_only: bool = True


@dataclass
class ReasoningRecord:
    """One line of the reasoning trace.

    Decision values:
        acquired    : included in the target list (first layer to claim it)
        also_serves : already acquired by a lower-tier layer; recorded as
                      additional layer-of-relevance for cross-layer
                      explainability without duplicate acquisition
        deferred    : reserved for future per-tier sub-phase reasoning
        omitted     : did not match any HVEA acquisition path
    """
    inventory_path: str
    decision: str
    layer: str | None
    tier: int | None
    matched_pattern: str | None
    dependency_context: list[str]
    rationale: str


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def load_graph(path: Path) -> HveaGraph:
    """Load and validate the HVEA graph JSON."""
    data = json.loads(path.read_text())

    tiers = {t["id"]: t for t in data["tiers"]}
    layers = {
        l["id"]: Layer(
            id=l["id"],
            name=l["name"],
            tier=l["tier"],
            purpose=l["purpose"],
            core_artifacts=l.get("core_artifacts", []),
            typical_sources=l.get("typical_sources", []),
            acquisition_paths=l.get("acquisition_paths", []),
        )
        for l in data["layers"]
    }
    deps = [
        Dependency(
            src=d["from"], dst=d["to"], type=d["type"],
            rationale=d["rationale"], strength=d.get("strength", "strong"),
        )
        for d in data.get("dependencies", [])
    ]

    # Validate every dependency references known layers.
    for d in deps:
        if d.src not in layers or d.dst not in layers:
            raise ValueError(
                f"Dependency {d.src}->{d.dst} references undefined layer."
            )

    g = HveaGraph(
        version=data["version"],
        tiers=tiers,
        layers=layers,
        dependencies=deps,
        convergence_patterns=data.get("convergence_patterns", []),
    )

    # Force-validate topology so cycles are caught at load time, not at run.
    g.topological_layer_order()
    logger.info("Loaded HVEA graph: %d layers, %d dependencies, version %s",
                len(layers), len(deps), data["version"])
    return g


# ---------------------------------------------------------------------------
# Inventory loader (DFXML — fiwalk output) with a JSONL fallback
# ---------------------------------------------------------------------------

def load_inventory(path: Path) -> list[InventoryItem]:
    """
    Load a file inventory.

    Supported formats:
      - DFXML (.xml / .dfxml) — fiwalk output from The Sleuth Kit
      - JSONL  (.jsonl)        — one {path, size, allocated} per line
                                 (useful for tests and synthetic runs)
    """
    suffix = path.suffix.lower()
    if suffix in {".jsonl", ".ndjson"}:
        items: list[InventoryItem] = []
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            items.append(InventoryItem(
                path=d["path"],
                size=int(d.get("size", 0)),
                allocated=bool(d.get("allocated", True)),
                inode=d.get("inode"),
            ))
        return items

    # DFXML
    items = []
    try:
        tree = ET.parse(path)
    except ET.ParseError as e:
        raise ValueError(f"Could not parse DFXML at {path}: {e}") from e

    root = tree.getroot()
    # fiwalk DFXML uses fileobject elements; namespace handling tolerant.
    for fo in root.iter():
        tag = fo.tag.split("}")[-1] if "}" in fo.tag else fo.tag
        if tag != "fileobject":
            continue
        filename = None
        size = 0
        allocated = True
        inode = None
        for child in fo:
            ctag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if ctag == "filename":
                filename = child.text
            elif ctag == "filesize":
                try:
                    size = int(child.text or 0)
                except (TypeError, ValueError):
                    size = 0
            elif ctag == "alloc":
                allocated = (child.text or "").strip() in {"1", "true", "True"}
            elif ctag == "inode":
                inode = (child.text or "").strip() or None
        if filename:
            # Normalize Windows backslashes to forward slashes.
            normalized = filename.replace("\\", "/")
            if not normalized.startswith("/"):
                normalized = "/" + normalized
            items.append(InventoryItem(
                path=normalized, size=size, allocated=allocated, inode=inode,
            ))
    return items


# ---------------------------------------------------------------------------
# Pattern matching
# ---------------------------------------------------------------------------

_GLOB_TOKEN = re.compile(r"\*\*|\*|\?")


def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    """
    Convert a small glob dialect to a regex.

    Supported:
      **  matches any sequence including '/'
      *   matches any sequence excluding '/'
      ?   matches a single character excluding '/'

    Comparison is case-insensitive because Windows filesystems are
    case-insensitive in practice.
    """
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


def _path_matches(path: str, pattern: str) -> bool:
    # Structural patterns like '$MFT' or '$Extend/$UsnJrnl:$J' don't have
    # a leading '/'. Some DFXML emitters include such entries in the file
    # inventory; match exactly when they do.
    if not pattern.startswith("/"):
        # Normalize: an inventory entry may be 'MFT' or '/$MFT' or '$MFT'.
        return path.lstrip("/") == pattern.lstrip("/")
    return bool(_glob_to_regex(pattern).match(path))


# ---------------------------------------------------------------------------
# Core reasoning
# ---------------------------------------------------------------------------

def reason_acquisition(
    graph: HveaGraph,
    inventory: list[InventoryItem],
) -> tuple[list[AcquisitionTarget], list[ReasoningRecord]]:
    """
    Produce a dependency-respecting ordered acquisition target list and the
    reasoning trace that explains every decision.

    Algorithm:
      1. Compute topological layer order from the HVEA graph.
      2. For each layer in that order, find inventory items matching the
         layer's acquisition_paths.
      3. If an inventory item is matched by a layer for the first time,
         create an AcquisitionTarget for it, stamped with a global sequence
         number and rationale. If a later layer also claims the same item,
         append the layer to the existing target rather than duplicate it.
      4. Inventory items that match no acquisition path are recorded in the
         trace as 'omitted' so the explainability metric has full visibility.
    """
    layer_order = graph.topological_layer_order()
    logger.info("Topological layer order: %s", " -> ".join(layer_order))

    targets_by_path: dict[str, AcquisitionTarget] = {}
    targets: list[AcquisitionTarget] = []
    trace: list[ReasoningRecord] = []
    layers_targeted_so_far: list[str] = []
    sequence = 0

    # Build an inventory-path index for filesystem-structure patterns.
    # Patterns like '$MFT' or '$Extend/$UsnJrnl:$J' identify structural
    # artifacts the acquisition mechanism can read directly; they may also
    # appear in the inventory (some DFXML emitters list them). We try to
    # match against the inventory first; if no inventory entry is found,
    # the structural pattern is still emitted as a target so the
    # acquisition mechanism can attempt the direct read.
    inv_paths = {inv.path for inv in inventory}

    for layer_id in layer_order:
        layer = graph.layers[layer_id]
        deps_satisfied = [
            d.src for d in graph.dependencies
            if d.dst == layer_id and d.src in layers_targeted_so_far
        ]

        for inv in inventory:
            for acq in layer.acquisition_paths:
                pattern = acq["pattern"]
                if not _path_matches(inv.path, pattern):
                    continue
                allocated_only = acq.get("allocated_only", True)
                if allocated_only and not inv.allocated:
                    continue

                existing = targets_by_path.get(inv.path)
                rationale = _build_acquisition_rationale(graph, layer, deps_satisfied)

                if existing is None:
                    sequence += 1
                    target = AcquisitionTarget(
                        inventory_path=inv.path,
                        matched_patterns=[pattern],
                        layers=[layer.id],
                        tiers=[layer.tier],
                        primary_layer=layer.id,
                        primary_tier=layer.tier,
                        sequence=sequence,
                        rationale=rationale,
                        dependencies_satisfied=deps_satisfied,
                        allocated_only=allocated_only,
                    )
                    targets.append(target)
                    targets_by_path[inv.path] = target
                    trace.append(ReasoningRecord(
                        inventory_path=inv.path,
                        decision="acquired",
                        layer=layer.id,
                        tier=layer.tier,
                        matched_pattern=pattern,
                        dependency_context=deps_satisfied,
                        rationale=rationale,
                    ))
                else:
                    # Already in the target list under a lower-numbered tier.
                    # Record that this layer also claims it, but do not emit
                    # a duplicate acquisition.
                    if layer.id not in existing.layers:
                        existing.layers.append(layer.id)
                        existing.tiers.append(layer.tier)
                        existing.matched_patterns.append(pattern)
                    trace.append(ReasoningRecord(
                        inventory_path=inv.path,
                        decision="also_serves",
                        layer=layer.id,
                        tier=layer.tier,
                        matched_pattern=pattern,
                        dependency_context=deps_satisfied,
                        rationale=(
                            f"Already acquired for Layer {existing.primary_layer} "
                            f"at sequence {existing.sequence}. This layer "
                            f"({layer.id}: {layer.name}) also relies on the same "
                            f"artifact for: {layer.purpose}"
                        ),
                    ))
                break  # one match per layer per inventory item is enough

        # After scanning the inventory for this layer, emit any structural
        # acquisition patterns (those without a leading '/') that didn't
        # match an inventory entry. These are filesystem-level artifacts
        # ($MFT, $UsnJrnl) the acquisition mechanism reads directly. Always
        # surface them as targets so Phase 3 can attempt them and so the
        # completeness metric correctly reflects that the layer was claimed.
        for acq in layer.acquisition_paths:
            pattern = acq["pattern"]
            if pattern.startswith("/"):
                continue
            # Already matched via inventory (rare but possible)?
            already_listed = any(pattern in t.matched_patterns for t in targets)
            if already_listed:
                continue
            sequence += 1
            rationale = _build_acquisition_rationale(graph, layer, deps_satisfied)
            target = AcquisitionTarget(
                inventory_path=pattern,
                matched_patterns=[pattern],
                layers=[layer.id],
                tiers=[layer.tier],
                primary_layer=layer.id,
                primary_tier=layer.tier,
                sequence=sequence,
                rationale=rationale + " [Filesystem-structure artifact; acquired directly by the mechanism, not via the inventory.]",
                dependencies_satisfied=deps_satisfied,
                allocated_only=acq.get("allocated_only", False),
            )
            targets.append(target)
            targets_by_path[pattern] = target
            trace.append(ReasoningRecord(
                inventory_path=pattern,
                decision="acquired",
                layer=layer.id,
                tier=layer.tier,
                matched_pattern=pattern,
                dependency_context=deps_satisfied,
                rationale=target.rationale,
            ))

        layers_targeted_so_far.append(layer_id)

    # Anything in the inventory we didn't match: log as omitted.
    matched_paths = set(targets_by_path)
    for inv in inventory:
        if inv.path in matched_paths:
            continue
        trace.append(ReasoningRecord(
            inventory_path=inv.path,
            decision="omitted",
            layer=None,
            tier=None,
            matched_pattern=None,
            dependency_context=[],
            rationale=(
                "No HVEA layer claims this path. Out of acquisition scope under "
                "the HVEA-driven selection model."
            ),
        ))

    return targets, trace


def _build_acquisition_rationale(
    graph: HveaGraph, layer: Layer, deps_satisfied: list[str]
) -> str:
    if deps_satisfied:
        dep_desc = ", ".join(
            f"Layer {d} ({graph.layers[d].name})" for d in deps_satisfied
        )
        return (
            f"Tier {layer.tier} - Layer {layer.id} ({layer.name}). {layer.purpose} "
            f"Predecessor layers already acquired: {dep_desc}."
        )
    return (
        f"Tier {layer.tier} - Layer {layer.id} ({layer.name}). {layer.purpose} "
        f"No predecessors required."
    )


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def write_targets(targets: list[AcquisitionTarget], path: Path) -> None:
    path.write_text(json.dumps(
        {"targets": [asdict(t) for t in targets]}, indent=2,
    ))


def write_trace(trace: list[ReasoningRecord], path: Path) -> None:
    with path.open("w") as fh:
        for r in trace:
            fh.write(json.dumps(asdict(r)) + "\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "HVEA reasoning module: produces a dependency-respecting "
            "acquisition target list from a baseline file inventory."
        ),
    )
    parser.add_argument("--graph", required=True, type=Path,
                        help="HVEA graph JSON (see hvea_schema.json).")
    parser.add_argument("--inventory", required=True, type=Path,
                        help="Baseline file inventory (DFXML or JSONL).")
    parser.add_argument("--out", required=True, type=Path,
                        help="Output: acquisition target list (JSON).")
    parser.add_argument("--trace", required=True, type=Path,
                        help="Output: reasoning trace (JSONL).")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    graph = load_graph(args.graph)
    inventory = load_inventory(args.inventory)
    logger.info("Loaded %d inventory items.", len(inventory))

    targets, trace = reason_acquisition(graph, inventory)
    write_targets(targets, args.out)
    write_trace(trace, args.trace)

    acquired = sum(1 for r in trace if r.decision == "acquired")
    also_serves = sum(1 for r in trace if r.decision == "also_serves")
    omitted = sum(1 for r in trace if r.decision == "omitted")
    logger.info(
        "Reasoning complete: %d acquired, %d multi-layer (also_serves), "
        "%d omitted. Targets: %s. Trace: %s.",
        acquired, also_serves, omitted, args.out, args.trace,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
