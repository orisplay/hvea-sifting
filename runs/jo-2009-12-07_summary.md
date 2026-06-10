# Jo Dec 7 — fully validated (eighth and final M57 image)

Date: 2026-06-10
Image SHA-256: 25a03ff768adf09e498e2c5773a20ec1d0b73cca438fb1017ff3873065a3767d
  (computed fresh; confirmed DISTINCT from the stale jo-2009-11-20-newComputer
   log entry 05b18f91... — a genuinely separate capture; recorded in master log)
Graph: hvea_graph_winxp.json
Partition offset: sector 63 (XP)

## Phase 1
- Inventory (after .. filter): ~34k (39,329 fileobjects pre-filter)
- Targets: 2,886; all ten layers; 0 traversal leaks
- Layer counts: A2 B7 C613 D1 E128 F1977 G601 H4 I1 J1

## Phase 3 acquisition
- Acquired: 2,388 files, 1,226 MB; not_found 392; failed 0; 7s

## Phase 5 validation (all pass; defensibility n/a pending rubric)
- Storage reduction: 0.249 (75% reduction)
- Artifact preservation (conservative): 0.865; Recoverable: 1.000
- Data-absent ghosts: 374 (mount-verified — most of any image); Genuine misses: 0
- Completeness: 1.0 (all 10 layers); Integrity: 1.0
- Transparency: full; Explainability: 1.0

## Jo cross-capture finding (old computer Nov 20 vs Dec 7)
Attribution/execution layers IDENTICAL across captures:
  A 2->2, B 7->7, E 128->128 (same to the digit)
Payload/residue layers shifted:
  C 773->613 (different content), G 434
