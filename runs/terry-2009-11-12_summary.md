# Terry Nov 12 — fully validated (completes Terry Vista pair)

Date: 2026-06-10
Image SHA-256: 3ecc178b03a41c2decaa6be732491f5bb616031fc84f25976e333cebbc82dcf1
Graph: hvea_graph_winvista.json
Partition offset: sector 2048 (Vista alignment)

## Phase 1
- Inventory (after .. filter): ~125k (151,423 fileobjects pre-filter)
- Targets: 1,465; all ten layers; 0 traversal leaks; ~99% omitted
- Layer counts: A2 B5 C41 D2 E120 F603 G660 H32 I1 J1

## Phase 3 acquisition
- Acquired: 1,305 files, 1,298 MB; not_found 77; failed 0; 6s

## Phase 5 validation (all pass; defensibility n/a pending rubric)
- Storage reduction: 0.180 (82% reduction)
- Artifact preservation (conservative): 0.962
- Recoverable preservation: 1.000
- Data-absent ghosts: 51 (mount-verified)
- Genuine misses: 0
- Completeness: 1.0 (all 10 layers); Integrity: 1.0
- Transparency: full; Explainability: 1.0

## Cross-temporal finding (Terry Nov 12 -> Nov 19): layers move in OPPOSITE directions
- F (browser): 603 -> 1308 (+705), browsing accumulated over the week
- G (deletion): 660 -> 369 (-291), MORE setup-cleanup residue on Nov 12
- E (execution): 120 -> 107 (~flat); C (content): 41 -> 45 (sparse both)
Unlike Charlie/Pat (all layers grew together), Terry's layers diverge:
behavioral accumulation (F up) vs transient-residue decay (G down). HVEA
distinguishes behavioral processes, not just gross activity level.

## Volume vs count
1,305 files but 1.3 GB (large files) vs Pat's 6,455 files / 827 MB (tiny
IE cache). File count and data volume are independent; reduction holds on both.

Six of eight validated (Charlie x2, Pat x2, Terry x2 — three temporal pairs).
Across all six: recoverable preservation 1.0, 0 genuine misses, integrity 1.0.
Only Jo x2 remaining.
