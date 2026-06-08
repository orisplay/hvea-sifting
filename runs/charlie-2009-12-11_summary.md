# Charlie Dec 11 — first real-evidence Phase 1+2 run

Date: 2026-06-07
Image: charlie-2009-12-11.E01 (M57-Patents)
Image SHA-256: (to be computed)
OS variant graph: hvea_graph_winxp.json

## Phase 1 (HVEA reasoning)
- Inventory items (fiwalk): 40,065
- Acquired (HVEA targets): 3,604
- Multi-layer (also_serves): 694
- Omitted: 36,384
- Selectivity: ~9% of inventory acquired

## Phase 1 layer coverage
A: 2, B: 7, C: 730, D: 1, E: 157, F: 2691, G: 615, H: 4, I: 1, J: 1
All ten layers represented. No graph adjustments required.

## Phase 2 (SIFTING profile)
- Groups: 4 (one per HVEA tier)
- Tier I  (A, B):           9 criteria, no deps
- Tier II (C):             730 criteria, deps [B]
- Tier III (E, F, G):    2,859 criteria, deps [B, C]
- Tier IV (H, I, J):         6 criteria, deps [B, C, D, E, G]

## Notes
- Layer F dominance (2,691) reflects Charlie Dec 11's heavy USPTO/WIPO
  browsing session documented in Paper II investigation notes.
- $MFT and $UsnJrnl surfaced as filesystem-structure targets (Phase 1
  structural-pattern emission worked as designed).
- No path-format mismatches between fiwalk DFXML and XP graph patterns.

## Status
Phase 3 (acquisition) and Phase 5 (validation) not yet executed.
