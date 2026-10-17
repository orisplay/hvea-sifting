# Terry Nov 12 — fully validated (completes Terry Vista pair)

Date: 2026-06-10
Image SHA-256: 3ecc178b03a41c2decaa6be732491f5bb616031fc84f25976e333cebbc82dcf1
  (computed fresh — was missing from m57-sha256.log; now recorded)
Graph: hvea_graph_winvista.json
Partition offset: sector 2048 (Vista alignment)

## Phase 1
- Inventory (after .. filter): ~125k (151,423 fileobjects pre-filter — largest yet)
- Targets: 1,465; all ten layers; 0 traversal leaks; ~99% omitted (most aggressive)
- Layer counts: A2 B5 C41 D2 E120 F603 G660 H32 I1 J1

## Phase 3 acquisition
- Acquired: 1,305 files, 1,298 MB; not_found 77; failed 0; 6s

## Phase 4 validation
| Metric | Value | Status |
|---|---|---|
| Storage reduction | 0.066 (93.4% reduction) | measured |
| Artifact preservation (conservative) | 0.962 | pass |
| Recoverable preservation | 1.000 | pass |
| Data-absent ghosts | 51 | mount-verified |
| Genuine misses | 0 | — |
| Completeness | 1.0 (all 10 layers) | pass |
| Integrity | 1.0 | pass |
| Transparency | full | pass |
| Explainability | 1.0 | pass |
| Defensibility | n/a | not scored |

## Cross-temporal finding (Terry Nov 12 -> Nov 19): layers move in OPPOSITE directions
| Layer | Nov 12 | Nov 19 | Change | Reading |
|---|---|---|---|---|
| F (browser) | 603 | 1,308 | +705 | browsing accumulated over the week |
| G (deletion) | 660 | 369 | -291 | MORE setup-cleanup residue on Nov 12 |
| E (execution) | 120 | 107 | -13 | ~flat |
| C (content) | 41 | 45 | +4 | sparse both (Terry = IT setup person) |

Unlike Charlie/Pat (all layers grew together over time), Terry's layers move
in opposite directions: behavioral accumulation (F up) vs transient-residue
decay (G down). The earlier setup-phase capture carried more deletion/temp
debris, cleared or overwritten by Nov 19. HVEA distinguishes behavioral
processes, not just gross activity level.

## Note on volume vs count
1,305 files but 1.3 GB — largest data volume, near-smallest file count.
Contrast Pat (6,455 files / 827 MB, tiny IE cache). File count and data
volume are independent axes; HVEA reduction holds on both.

## Findings
- Vista-variant graph validated on a second image (after Nov 19): all 10
  layers, 0 leaks, no adjustment. Vista architecture robust across captures.
- Leanest selectivity of the corpus: ~99% omitted on a 41 GB disk.
- Recoverable preservation 1.0, 0 genuine misses, 51 mount-verified ghosts.

Completes the Terry Vista pair (3rd of 4 temporal/cross pairs).
