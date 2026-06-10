# HVEA-SIFTING — Master Validation Results (all 9 images)

Generated: 2026-06-10
Storage-reduction denominator: **ewfinfo media size** (corrected; see note below).

## Corpus summary

| Image | OS | Media | Acquired | Storage reduction | Recoverable preservation | Genuine misses | Integrity | Layers |
|---|---|---|---|---|---|---|---|---|
| charlie-2009-11-12 | XP | 10.24 GB | 730 MB | **92.5%** (0.0748) | 1.000 | 0 | 1.0 | 10/10 |
| charlie-2009-12-11 | XP | 10.24 GB | 1.1 GB | **89.5%** (0.1052) | 1.000 | 0 | 1.0 | 10/10 |
| pat-2009-11-16 | XP | 13.02 GB | 791 MB | **93.6%** (0.0637) | 1.000 | 0 | 1.0 | 10/10 |
| pat-2009-11-17 | XP | 13.02 GB | 827 MB | **93.3%** (0.0666) | 1.000 | 0 | 1.0 | 10/10 |
| jo-2009-11-20-oldComputer | XP | 13.02 GB | 1.1 GB | **90.8%** (0.0916) | 1.000 | 0 | 1.0 | 10/10 |
| jo-2009-12-07 | XP | 15.38 GB | 1.2 GB | **91.6%** (0.0836) | 1.000 | 0 | 1.0 | 10/10 |
| terry-2009-11-12 | Vista | 20.53 GB | 1.3 GB | **93.4%** (0.0663) | 1.000 | 0 | 1.0 | 10/10 |
| terry-2009-11-19 | Vista | 41.11 GB | ~1.0 GB | **97.4%** (0.0260) | 1.000 | 0 | 1.0 | 10/10 |
| W11_HVEA_14D | Win11 | 40.00 GB | 4.5 GB | **89.0%** (0.1105) | 1.000 | 0 | 1.0 | 10/10 |

## Headline findings

- **Storage reduction: 89.0%–97.4%** across the corpus (mean ~92%), measured
  against true media size. HVEA-SIFTING reliably acquires ~3–11% of the disk
  while preserving every recoverable targeted artifact.
- **Recoverable preservation = 1.000 on every image.** Every targeted file that
  still held data was acquired. All unacquired targets were mount-verified
  data-absent MFT ghosts (51–461 per image, tracking each image's deletion
  activity); **0 genuine misses anywhere in the corpus.**
- **Integrity = 1.000 on every image.** Bit-for-bit hash match between acquired
  files and source, across three NTFS generations.
- **Completeness = all 10 HVEA layers on every image.**
- **Transparency = full; Explainability = 1.000** on every image.
- **Three OS variants** (XP SP3, Vista SP2, Windows 11) validated with their
  respective HVEA graphs; each graph populated all ten layers first-try with
  no adjustment.
- **Defensibility = n/a** on every image, by design, pending advisor rubric
  approval. Once approved, Phase 5 re-runs populate this metric without
  re-acquisition.

## Cross-image findings

- **Temporal pairs (Charlie, Pat):** HVEA acquisition footprint tracks behavioral
  change over time (setup day vs research day; day-to-day escalation at the layer
  level — Pat's Layer F/E grew with documented browsing/tool activity).
- **Terry (Vista) pair:** layers move in opposite directions across captures —
  browser layer accumulates (F up) while deletion residue decays (G down) as
  setup-phase debris clears. HVEA distinguishes behavioral *processes*, not just
  activity level.
- **Jo cross-capture:** attribution and execution layers identical across two
  separate captures of the same person (A, B, E unchanged) while payload/residue
  layers vary (C, G). Tier separation working as designed: attribution stable,
  behavior variable.
- **Ghost/Layer-G consistency:** images with high deletion-residue (Layer G) have
  proportionally high data-absent ghost counts (e.g. Jo Dec 7: G=601, 374 ghosts;
  Win11: G=1957, 461 ghosts), all mount-verified. Two independent signals agree.

## Note on the storage-reduction correction

The first multi-segment image (Windows 11, 18 E01 segments) exposed a denominator
bug in the validation harness: baseline size was measured from the `.E01` file on
disk rather than the logical media size. For single-segment M57 images the `.E01`
file ≈ media size, so the error was modest (each image's reduction was understated
by ~13–18 percentage points); for the multi-segment Win11 image the `.E01` was
1/25th of the media, which inverted the ratio (reported 3.0). The harness now reads
the logical media size via `ewfinfo` (source-tagged `ewfinfo_media_size`) with a
mounted-partition fallback. All nine images were re-validated under the corrected
metric; only storage_reduction changed — integrity, preservation, completeness,
transparency, and explainability were unaffected and re-confirmed identical.

Previously reported (buggy) range: 70–86%. Corrected range: 89.0–97.4%.
