# Jo old computer (Nov 20) — fully validated

Date: 2026-06-10
Image SHA-256: c141e380cb8e642dc5a905f253577dcf3dc205ebe97383ac00f2a18c6e3031cf
  (verified against master log before acquisition — bit-for-bit match)
Graph: hvea_graph_winxp.json
Partition offset: sector 63 (XP)

## Phase 1
- Inventory (after .. filter): ~33k (37,641 fileobjects pre-filter)
- Targets: 2,882; all ten layers; 0 traversal leaks
- Layer counts: A2 B7 C773 D1 E128 F1962 G434 H4 I1 J1

## Phase 3 acquisition
- Acquired: 2,672 files, 1,137 MB; not_found 99; failed 0; 14s

## Phase 5 validation (all pass; defensibility n/a pending rubric)
- Storage reduction: 0.298 (70% reduction — most modest, richest content layer)
- Artifact preservation (conservative): 0.968; Recoverable: 1.000
- Data-absent ghosts: 89 (mount-verified); Genuine misses: 0
- Completeness: 1.0 (all 10 layers); Integrity: 1.0
- Transparency: full; Explainability: 1.0

## Note
Jo is the cross-MACHINE pair (old computer vs new computer Dec 7), not a
temporal pair. Layer C = 773 (richest user content of the XP subjects) ->
lower reduction because more of the disk is genuinely evidentiary. Layer B
(identity) = 7; to be compared against Dec 7 new computer for attribution
consistency across machines.

Seven of eight M57 images validated. Across all seven: recoverable
preservation 1.0, 0 genuine misses, integrity 1.0, all 10 layers.
