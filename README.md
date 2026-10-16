# HVEA-SIFTING

**Dependency-Driven Selective Acquisition and Negative-Space Auditing for Defensible Windows Forensic Imaging**

Research code, configuration, and validation artifacts for Paper III of the dissertation
*"Defensible Intelligent Imaging and Reduction for Scalable Digital Forensics."*

> \*\*Status:\*\* Public. This repository accompanies the submitted manuscript and is released to
> permit independent reproduction of the reasoning, acquisition, and negative-space audit. A
> versioned Zenodo DOI will be minted at publication.

## What this is

HVEA-SIFTING is a four-phase selective-acquisition pipeline that uses the **High-Value Evidence
Areas (HVEA)** dependency model (Paper II) as its selection basis. Rather than deciding relevance
by flat criteria: file type, disk region, or investigator choice, it acquires artifacts in
**evidentiary-dependency order** across ten layers and four tiers, so that each acquired item is
interpretable in the context its predecessors establish.

The work makes two contributions:

1. **Dependency-driven acquisition.** To our knowledge, the first use of an inter-artifact
evidentiary-dependency model to *drive* selective acquisition, rather than to analyze evidence
already collected.
2. **A reproducible negative-space audit.** A deterministic, file-level classification of
everything the method *omits*, so the soundness of the omission is measured rather than assumed.

Evaluated on nine Windows images (eight from the public M57-Patents corpus spanning XP and Vista,
plus a controlled Windows 11 image), the pipeline reduced acquired volume by 89.0-97.4% at
bit-for-bit integrity, preserved every recoverable targeted artifact with zero genuine misses,
and populated all ten HVEA layers on every image. The negative-space audit found no user-authored
content among hundreds of thousands of omitted entries.

## Companion papers

* **Paper I** - *Where Intelligence Has Taken Hold, and Where It Has Not: A PRISMA-Guided
Systematic Mapping Review of Digital Forensics.* Electronics, 2026.
Establishes the field-level defensibility vocabulary (completeness, integrity, transparency,
explainability, defensibility) that this work's validation harness operationalizes.
* **Paper II** - *A Layered High-Value Evidence Area (HVEA) Model for Selective Windows Digital
Forensics Imaging.* Electronics, 2026.
Defines the ten artifact layers, four tiers, and evidentiary dependencies that Paper III
formalizes into an executable reasoning graph.

## Repository layout

```
paperiii/
    phase1\_hvea\_graph/        Formal HVEA dependency graph + reasoner
        hvea\_schema.json          JSON Schema for the graph
        hvea\_graph\_winxp.json     XP variant (Charlie, Jo, Pat)
        hvea\_graph\_winvista.json  Vista variant (Terry)
        hvea\_graph\_win11.json     Windows 11 variant (controlled set)
        hvea\_reasoner.py          Topological reasoning module (Eq. 1)
    phase2\_sifting\_mapping/   Acquire decisions -> tiered acquisition profile
        sifting\_profile\_mapper.py
    phase3\_acquisition/       Dependency-ordered acquisition harness
        acquisition\_harness.py
    phase4\_validation/        Eight-metric validation harness
        validation\_harness.py
    docs/
        M57\_Win11\_Pilot\_Protocol.md   Step-by-step per-image protocol

audit/                        Negative-space audit
    classify\_omitted.py           Deterministic omitted-set classifier
    residues/                     Complete flagged-residue listings (XP, Vista, Win11)
    AUDIT\_\*.md                    Per-image audit write-ups

runs/
    traces/                       HVEA reasoning traces for the eight M57 images
    \*\_summary.md                  Per-image validation summaries

hashes/                       Source-image SHA-256 (chain of custody)
logs/                         Per-image logs (gitignored; .gitkeep retained)
```

## What is and isn't in git

**Tracked.** All code, all HVEA graphs, the deterministic negative-space classifier, the complete
flagged-residue listings, the per-image reasoning traces for the eight M57 images, the per-image
validation summaries, and the source-image SHA-256 hashes (chain of custody).

**Not tracked.** Evidence images (`\*.E01`, `\*.dd`), regenerable baseline DFXML inventories, and
acquired partial-image trees (tens of GB). The M57 dataset is publicly distributed, so the data
itself is not sensitive; the exclusions are purely about volume. The repository holds the means to
reconstruct every result. Exclusions are documented in `.gitignore`.

## Reproducing the pipeline

The end-to-end per-image workflow is in `paperiii/docs/M57\_Win11\_Pilot\_Protocol.md`: hash and mount
the image, generate a fiwalk DFXML inventory, run Phase 1 (reasoning), Phase 2 (profile), Phase 3
(acquisition), and Phase 4 (validation).

The negative-space classification can be reproduced directly from the committed traces:

```bash
python3 audit/classify\_omitted.py runs/traces/jo-2009-11-20-oldComputer\_hvea\_reasoning.jsonl
```

Traces are included for all eight M57 images (charlie ×2, jo ×2, pat ×2, terry ×2). The controlled
Windows 11 image and its reasoning trace contain synthetic activity generated for this study and
are available from the corresponding author on reasonable request.

## Datasets

* **M57-Patents** (Charlie, Jo, Pat, Terry × two captures each) - Windows XP SP3 and
Vista Business SP2 images from the publicly distributed M57 scenario.
* **W11\_HVEA\_14D** - controlled Windows 11 image, 14-day activity protocol.

## Citation

Aigbogun, O. O.; Varol, C.; Shashidhar, N. *HVEA-SIFTING: Dependency-Driven Selective Acquisition
and Negative-Space Auditing for Defensible Windows Forensic Imaging.* 2026. (DOI pending.)

## License

Code is released under the MIT License (see `LICENSE`). Documentation and figures are released under
CC-BY-4.0.

## Acknowledgements

Built on the M57-Patents corpus and the DFXML toolset (Garfinkel) and The Sleuth Kit / fiwalk
(Carrier). Prior selective-imaging work by Grier \& Richard (sifting collectors, DFRWS 2015)
situates this contribution. Independent expert review by Yazen Aswad (Elite Forensics LLC) and
Orhan Duran (Turkish National Police) strengthened the defensibility analysis. Developed under the
supervision of Dr. C. Varol and Dr. N. Shashidhar.

