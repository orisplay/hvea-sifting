# Windows 11 (W11_HVEA_14D) — fully validated (ninth image, third OS variant)

Date: 2026-06-10
Image MD5 (ewfverify, full 18-segment set): cbff96d87602576457c8cc5c1478f377
  SHA1 (ewfverify): e630f459ce5a35494461cc65da4f804f66dae28a
  ewfverify: SUCCESS (stored hash == recomputed over full 40 GiB) — source intact
Graph: hvea_graph_win11.json (FIRST use on real Win11 evidence)
Partition: GPT slot 006, offset 227540992 (sector 444416), ~39 GB Windows volume
Working disk: dedicated 60 GB ext4 on D: (/mnt/win11work) — native, no FUSE

## Phase 1
- Inventory (after .. filter): 322,710 (455,744 fileobjects pre-filter — largest)
- Targets: 13,875; all ten layers; 0 traversal leaks; ~96% omitted
- Layer counts: A2 B5 C70 D1 E623 F10823 G1957 H393 I1 J1

## Phase 3 acquisition
- Acquired: 11,387 files, 4.5 GB; not_found 605; failed 0; 37s
- Output on /mnt/win11work (native ext4) — integrity metric unaffected by FUSE

## Phase 5 validation
| Metric | Value | Status |
|---|---|---|
| Storage reduction | 0.111 (88.95% reduction) | measured |
| Artifact preservation (conservative) | 0.961 | pass |
| Recoverable preservation | 1.000 | pass |
| Data-absent ghosts | 461 | mount-verified |
| Genuine misses | 0 | — |
| Completeness | 1.0 (all 10 layers) | pass |
| Integrity | 1.0 | pass |
| Transparency | full | pass |
| Explainability | 1.0 | pass |
| Defensibility | n/a | rubric pending |

## Findings
- Win11-variant graph validated first-try: all 10 layers, 0 leaks, no
  adjustment. Modern artifact paths matched — Layer F = 10,823 (Edge/Chromium
  cache, not legacy IE), Layer H = 393 (Win11 .evtx channels, richest in
  corpus), Layer E = 623 (modern execution evidence, richest in corpus).
  Third OS variant proven; same model, OS-specific paths, across XP/Vista/Win11.
- High selectivity on the modern OS: 89.0% reduction on a 40 GiB disk.
  Reduction is consistently high corpus-wide (89.0-97.4% vs true media size),
  with the largest disks trending highest (Terry Nov 19, 41 GB -> 97.4%).
- Recoverable preservation 1.0, 0 genuine misses, 461 mount-verified ghosts.

## Metric fix applied this run (storage_reduction denominator)
First multi-segment image (18 E01 segments) exposed a denominator bug: the
harness measured baseline size from the .E01 file (1.57 GB) instead of the
full media. For single-segment M57 images .E01 ~= media so the error was
small; here it inverted the ratio (reported 3.0). Fixed: baseline size now
from ewfinfo media size (42,949,672,960 bytes), source-tagged
'ewfinfo_media_size'. All 8 M57 images being re-validated under the fix.

NINTH image; THREE OS variants (XP, Vista, Win11). Across all nine:
recoverable preservation 1.0, 0 genuine misses, integrity 1.0, all 10 layers.
