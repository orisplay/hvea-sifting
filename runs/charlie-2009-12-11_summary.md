# Charlie Dec 11 — clean run (post traversal-fix)

Date: 2026-06-08
Image SHA-256: 7f4ae8676e28ed76034392c68831a0948b4b40788070ad2ed660f32b045e2b5b
Graph: hvea_graph_winxp.json

## Phase 1
- Inventory (after .. filter): 33,882 (was 40,065 pre-filter)
- Targets: 3,280; multi-layer: 568; omitted: 30,525
- Layers: A2 B7 C562 D1 E149 F2549 G483 H4 I1 J1 (all ten)

## Phase 3 acquisition
- Acquired: 3,055 files, 1.1 GB
- not_found: 115, failed: 0
- Duration: 25s
- vs buggy run: 106,062 files / 15 GB / 298s

## Finding
Real selectivity ~1.1 GB acquired vs ~6 GB meaningful disk (~82% reduction),
all ten HVEA layers preserved. Prior 15 GB was the /RECYCLER/.. traversal
escape (fixed, commit 40d20fe). Layer F (browser, 2,549 targets) dominates —
consistent with Charlie's patent-research browsing footprint.

## Status: Phase 5 validation pending.
