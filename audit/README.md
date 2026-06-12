# HVEA-SIFTING Negative-Space Audit

This directory substantiates the claim that HVEA-driven selective imaging omits
**no forensically relevant data** — i.e., that the disk content *not* acquired is
inert (operating-system, application, and system files), and that user-authored
evidentiary content is acquired wherever it exists.

## What this is

For each audited image, every inventory entry HVEA examined carries an explicit
acquire/omit decision (the Phase 1 reasoning trace). This audit takes the
complete **omitted** set, classifies each entry by path into
forensically-meaningful categories using a deterministic rule set
(`classify_omitted.py`), and then **individually inspects** every entry that could
plausibly hold user-authored content. The residual flagged paths are recorded in
full under `residues/` so the classification can be independently verified.

## Method

1. Load the reasoning trace; take all records with `decision == "omitted"`.
2. Classify each path (OS core, installed apps, system cache, fonts, recovery,
   registry journals, user-space app cache, OS-seeded defaults, directory stubs,
   etc.). The classifier handles both the `Users\` (Vista/Win11) and
   `Documents and Settings\` (XP) profile layouts.
3. Anything not matching an inert pattern is flagged `USER CONTENT (REVIEW)` or
   `UNCLASSIFIED (REVIEW)` and enumerated in `residues/` for manual inspection.
4. Separately, confirm HVEA's Layer C **acquired** the user's real content
   (documents, downloads, media) on the same image.

## Results across three OS variants

| Image | OS | Omitted | Classified inert | User-authored files omitted | Real content acquired |
|---|---|---|---|---|---|
| W11_HVEA_14D | Windows 11 | 308,833 | 99.99% | **0** | documents, downloaded installers |
| jo-2009-11-20 | Windows XP | 28,782 | 99.16% | **0** | 1,060 files incl. camera photos & video |
| terry-2009-11-12 | Windows Vista | 116,745 | 99.96% | **0** | 1,257 entries incl. downloaded installer |

Every flagged user-space entry, on every image, was inspected and confirmed
non-evidentiary: OS sample media (XP/Vista stock pictures, music, video), blank
application templates, default IE/MSN bookmarks, registry hive journals, IE cache
indices, and empty directory stubs. The signature demonstration is on the
content-rich XP image, where HVEA acquired the user's real digital-camera
photographs (`Desktop/Pics/DSC*.JPG`) while omitting the operating system's stock
`Sample Pictures/Blue hills.jpg` — evidentiary discrimination, not volumetric
reduction.

## Files

- `classify_omitted.py` — the deterministic classifier (input: a Phase 1
  reasoning trace; output: category breakdown + enumerated residue).
- `AUDIT_win11.md`, `AUDIT_jo_xp.md`, `AUDIT_terry_vista.md` — per-image reports.
- `residues/` — the complete enumerated flagged-path list for each image.

## Reproducing

The reasoning traces are large and are not version-controlled. With a trace
present, regenerate any image's classification with:

    python3 classify_omitted.py <reasoning_trace>.jsonl <output_residue>.txt
