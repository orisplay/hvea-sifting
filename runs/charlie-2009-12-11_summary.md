# Charlie Dec 11 — fully validated (research-day capture)

Date: 2026-06-08
Image SHA-256: 7f4ae8676e28ed76034392c68831a0948b4b40788070ad2ed660f32b045e2b5b
Graph: hvea_graph_winxp.json

## Phase 1
- Inventory (after .. filter): 33,882
- Targets: 3,280; all ten layers represented

## Phase 3 acquisition
- Acquired: 3,054 files, 1.1 GB; not_found 115; failed 0; 25s

## Phase 4 validation
| Metric | Value | Status |
|---|---|---|
| Storage reduction | 0.105 (89.5% reduction) | measured |
| Artifact preservation (conservative) | 0.969 | pass |
| Recoverable preservation | 1.000 | pass |
| Data-absent ghosts | 97 | mount-verified |
| Genuine misses | 0 | — |
| Completeness | 1.0 (all 10 layers) | pass |
| Integrity | 1.0 | pass |
| Transparency | full | pass |
| Explainability | 1.0 | pass |
| Defensibility | n/a | not scored |

## Finding
Recoverable preservation 1.0: every targeted file with recoverable data
was acquired. The 97 unacquired targets are mount-verified MFT ghosts.
Research-day capture: 3,280 targets, Layer F (browser) 2,549 — heavier
than Nov 12 setup day, consistent with USPTO/WIPO patent-research session.
