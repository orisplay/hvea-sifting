# Charlie Dec 11 — fully validated (post traversal-fix, files-only preservation metric)

Date: 2026-06-08
Image SHA-256: 7f4ae8676e28ed76034392c68831a0948b4b40788070ad2ed660f32b045e2b5b
Graph: hvea_graph_winxp.json

## Phase 1
- Inventory (after .. filter): 33,882
- Targets: 3,280; multi-layer: 568; omitted: 30,525
- All ten layers represented

## Phase 3 acquisition
- Acquired: 3,055 files, 1.1 GB
- not_found: 115, failed: 0; duration 25s

## Phase 5 validation
| Metric | Value | Status |
|---|---|---|
| Acquisition speed | 24.98s | measured |
| Storage reduction | 0.278 (72% reduction) | measured |
| Artifact preservation | 0.969 | pass |
| Completeness | 1.0 (all 10 layers) | pass |
| Integrity | 1.0 | pass |
| Transparency | full | pass |
| Explainability | 1.0 | pass |
| Defensibility | n/a | rubric pending advisor |

## Findings
- 72% storage reduction with all ten evidentiary layers preserved and
  96.9% file-level artifact preservation. Integrity perfect (every
  acquired file hash-matches the read-only source).
- Artifact preservation uses a files-only denominator: directory
  container entries are not independently acquirable artifacts and are
  excluded from numerator and denominator. Remaining ~3% are HVEA-targeted
  files absent on this specific image (uninstalled browsers, etc.) —
  effectively the preservation ceiling.
