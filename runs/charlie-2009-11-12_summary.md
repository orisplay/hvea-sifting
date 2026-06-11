# Charlie Nov 12 — fully validated (setup-day capture)

Date: 2026-06-08
Image SHA-256: ad2f61d34627d5687583a22a410721f2b2b5b52a753905d474f08e1747225598
Graph: hvea_graph_winxp.json

## Phase 1
- Inventory (after .. filter): 28,970
- Targets: 1,488; all ten layers represented

## Phase 3 acquisition
- Acquired: 1,283 files, 730 MB; not_found 110; failed 0; 6s

## Phase 5 validation
| Metric | Value | Status |
|---|---|---|
| Storage reduction | 0.075 (92.5% reduction) | measured |
| Artifact preservation (conservative) | 0.927 | pass |
| Recoverable preservation | 1.000 | pass |
| Data-absent ghosts | 101 | mount-verified |
| Genuine misses | 0 | — |
| Completeness | 1.0 (all 10 layers) | pass |
| Integrity | 1.0 | pass |
| Transparency | full | pass |
| Explainability | 1.0 | pass |
| Defensibility | n/a | rubric pending |

## Finding
Recoverable preservation 1.0: every targeted file with recoverable data
was acquired. The 101 unacquired targets are MFT-resident entries with no
recoverable data, verified absent by direct mount inspection — not
preservation failures. Cross-temporal: this setup-day capture selected
1,488 targets vs Dec 11's 3,280, with Layer F (browser) 896 vs 2,549,
tracking the documented behavioral difference (setup day vs research day).
