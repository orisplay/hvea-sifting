# Pat Nov 17 — fully validated (completes Pat temporal pair)

Date: 2026-06-10
Image SHA-256: c24db50fbf8ae60946f2034f1fd595a4d99a6320a491554120391f4639bfe9c9
Graph: hvea_graph_winxp.json
Partition offset: sector 63 (XP)

## Phase 1
- Inventory (after .. filter): ~34.7k (39,884 fileobjects pre-filter)
- Targets: 6,659; all ten layers; 0 traversal leaks
- Layer counts: A2 B7 C479 D1 E108 F6057 G432 H4 I1 J1

## Phase 3 acquisition
- Acquired: 6,455 files, 827 MB; not_found 97; failed 0; 10s

## Phase 4 validation
| Metric | Value | Status |
|---|---|---|
| Storage reduction | 0.067 (93.3% reduction) | measured |
| Artifact preservation (conservative) | 0.987 | pass |
| Recoverable preservation | 1.000 | pass |
| Data-absent ghosts | 87 | mount-verified |
| Genuine misses | 0 | — |
| Completeness | 1.0 (all 10 layers) | pass |
| Integrity | 1.0 | pass |
| Transparency | full | pass |
| Explainability | 1.0 | pass |
| Defensibility | n/a | not scored |

## Cross-temporal finding (Pat Nov 16 -> Nov 17)
HVEA tracked Pat's documented day-to-day behavioral escalation at the
LAYER level:
| Layer | Nov 16 | Nov 17 | Change | Documented cause |
|---|---|---|---|---|
| Total | 6,387 | 6,659 | +272 | more activity Nov 17 |
| F (browser) | 5,807 | 6,057 | +250 | LANL/NIH/NASA research session |
| E (execution) | 88 | 108 | +20 | MDD runs 2->4, new tools |
| C (content) | 477 | 479 | +2 | new web/ folder (webauto.py) |
Stable layers (A,B,D,G,H,I,J) stayed flat. Selectivity is sensitive to
specific behavioral change, not just gross disk differences. Second clean
temporal pair (after Charlie); Pat's is finer-grained per Paper II notes.

Five of eight M57 images validated. Across all five: recoverable
preservation 1.0, 0 genuine misses, integrity 1.0, all 10 layers.
