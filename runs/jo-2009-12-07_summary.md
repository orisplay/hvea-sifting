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

## Phase 5 validation
| Metric | Value | Status |
|---|---|---|
| Storage reduction | 0.249 (75% reduction) | measured |
| Artifact preservation (conservative) | 0.865 | pass |
| Recoverable preservation | 1.000 | pass |
| Data-absent ghosts | 374 | mount-verified |
| Genuine misses | 0 | — |
| Completeness | 1.0 (all 10 layers) | pass |
| Integrity | 1.0 | pass |
| Transparency | full | pass |
| Explainability | 1.0 | pass |
| Defensibility | n/a | rubric pending |

## Cross-capture finding (Jo old computer Nov 20 vs Dec 7): attribution stable, behavior varies
| Layer | Jo old (Nov 20) | Jo Dec 7 | Reading |
|---|---|---|---|
| A (system) | 2 | 2 | identical — same baseline structure |
| B (identity) | 7 | 7 | identical — same person's identity signature |
| E (execution) | 128 | 128 | identical to the digit |
| F (browser) | 1,962 | 1,977 | ~flat (+15) |
| C (content) | 773 | 613 | -160 (different content) |
| G (deletion) | 434 | 601 | +167 (more deletion activity) |

HVEA's attribution tier (A, B) and execution telemetry (E) produce an
IDENTICAL signature across two separate captures of the same person, while
the payload/residue tiers (C, G) reflect the actual differences. Tier
separation working as designed: attribution stable, behavior variable.
None of the same-machine temporal pairs could demonstrate this.

## On the high ghost count
374 data-absent ghosts — most of any image (others 51-113) — tracks Layer G
= 601 (high deletion residue, 2nd-highest in corpus). Many MFT entries point
at deleted/overwritten content. All 374 mount-verified absent; recoverable
preservation still 1.0. Two independent signals agree (high G -> high
ghosts), an internal consistency check on the framework.

## Findings
- Attribution-stability across captures (above) — a property unique to the
  cross-capture Jo pair.
- High-deletion image: ghost count and Layer G corroborate each other.
- Recoverable preservation 1.0, 0 genuine misses, integrity 1.0, all 10 layers.

ALL EIGHT M57 images validated (Charlie x2, Pat x2, Terry x2, Jo x2).
Across all eight: recoverable preservation 1.0, 0 genuine misses, integrity
1.0, all 10 layers, both OS variants (XP + Vista). Only the Windows 11
image remains (needs dedicated storage first).
