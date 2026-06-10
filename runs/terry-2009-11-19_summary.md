# Terry Nov 19 — fully validated (first Vista image)

Date: 2026-06-10
Image SHA-256: bb385b548c1e4953c4c393c1bcf3c2e0e4d4fcd3b4c8954ef874336ba088ab8f
Graph: hvea_graph_winvista.json (FIRST use of Vista variant on real evidence)
Partition offset: sector 2048 (Vista alignment; XP was 63)

## Phase 1
- Inventory (after .. filter): 99,047 (124,878 fileobjects pre-filter; ~25.8k dot-entries stripped)
- Targets: 1,868; all ten layers represented; 0 traversal leaks
- Layer counts: A2 B5 C45 D2 E107 F1308 G369 H30 I1 J1

## Phase 3 acquisition
- Acquired: 1,673 files, ~1.0 GB; not_found 110; failed 0; 9s

## Phase 5 validation
| Metric | Value | Status |
|---|---|---|
| Storage reduction | 0.136 (86% reduction) | measured |
| Artifact preservation (conservative) | 0.949 | pass |
| Recoverable preservation | 1.000 | pass |
| Data-absent ghosts | 90 | mount-verified |
| Genuine misses | 0 | — |
| Completeness | 1.0 (all 10 layers) | pass |
| Integrity | 1.0 | pass |
| Transparency | full | pass |
| Explainability | 1.0 | pass |
| Defensibility | n/a | rubric pending |

## Findings
- Vista-variant HVEA graph validated first-try on real evidence: all ten
  layers, 0 traversal leaks, no graph adjustment needed. Confirms the
  same-model/OS-specific-paths architecture across two Windows generations.
- Leanest selectivity yet: 86% reduction on a 41 GB Vista disk. HVEA's
  advantage scales with disk size — the larger/more system-heavy the disk,
  the greater the proportional reduction (XP ~72-76%, Vista 86%).
- Layer H = 30 (vs XP's 4): Vista's granular .evtx event channels, all
  caught by the winevt/Logs path. Layer C = 45 (sparse user content),
  consistent with Terry as the IT setup person rather than a document user.
- Recoverable preservation 1.0, 0 genuine misses, 90 mount-verified ghosts.
