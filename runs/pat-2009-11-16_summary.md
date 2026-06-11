# Pat Nov 16 — fully validated (browser-heavy XP subject)

Date: 2026-06-10
Image SHA-256: c9c05c3203073ff9414362b50333ea35c798b26720354f40aebb79c95765faed
  (computed fresh — was missing from m57-sha256.log; now recorded)
Graph: hvea_graph_winxp.json
Partition offset: sector 63 (XP)

## Phase 1
- Inventory (after .. filter): 34,241 (39,328 fileobjects pre-filter)
- Targets: 6,387; all ten layers; 0 traversal leaks
- Layer counts: A2 B7 C477 D1 E88 F5807 G437 H4 I1 J1

## Phase 3 acquisition
- Acquired: 6,159 files, 791 MB; not_found 123; failed 0; 9s

## Phase 5 validation
| Metric | Value | Status |
|---|---|---|
| Storage reduction | 0.064 (93.6% reduction) | measured |
| Artifact preservation (conservative) | 0.982 | pass |
| Recoverable preservation | 1.000 | pass |
| Data-absent ghosts | 113 | mount-verified |
| Genuine misses | 0 | — |
| Completeness | 1.0 (all 10 layers) | pass |
| Integrity | 1.0 | pass |
| Transparency | full | pass |
| Explainability | 1.0 | pass |
| Defensibility | n/a | rubric pending |

## Findings
- Browser-heavy subject: Layer F = 5,807 targets, ~91% of acquisition,
  4,914 of them in Pat's IE Content.IE5 cache. Verified as genuine browser
  artifacts (not pattern over-match) by path-cluster inspection. HVEA's
  Layer F correctly scales to capture a full browser footprint when present.
- High file count (6,159) but smallest data volume (791 MB) of any image —
  IE cache objects are numerous but tiny. 93.6% storage reduction (vs true media size) holds.
- Recoverable preservation 1.0, 0 genuine misses, 113 mount-verified ghosts
  (most yet — dense IE cache churns the most MFT entries).
- Hash was missing from the master log; computed fresh and recorded.

Four of eight M57 images validated (Charlie x2, Terry, Pat). Across all
four: recoverable preservation 1.0, 0 genuine misses, integrity 1.0.
