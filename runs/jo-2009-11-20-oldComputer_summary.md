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

## Phase 5 validation
| Metric | Value | Status |
|---|---|---|
| Storage reduction | 0.092 (90.8% reduction) | measured |
| Artifact preservation (conservative) | 0.968 | pass |
| Recoverable preservation | 1.000 | pass |
| Data-absent ghosts | 89 | mount-verified |
| Genuine misses | 0 | — |
| Completeness | 1.0 (all 10 layers) | pass |
| Integrity | 1.0 | pass |
| Transparency | full | pass |
| Explainability | 1.0 | pass |
| Defensibility | n/a | rubric pending |

## Findings
- Richest user-content layer of the XP subjects: Layer C = 773. This drives
  the most modest reduction in the corpus (70%) — when more of the disk is
  genuinely evidentiary, HVEA correctly preserves proportionally more.
- Source hash re-verified against the master log before acquisition
  (bit-for-bit match) — chain-of-custody confirmation step.
- Recoverable preservation 1.0, 0 genuine misses, 89 mount-verified ghosts,
  integrity 1.0, all 10 layers.

## Note on the Jo pair
Jo is the cross-MACHINE / cross-capture pair (old computer Nov 20 vs a
separate Dec 7 capture), not a same-machine temporal pair. Layer B (identity)
= 7 here; compared against Dec 7 in that image's summary, where the
attribution-stability finding is recorded.

Seventh of eight M57 images.
