# Paper III — HVEA-Enhanced SIFTING

> **Status:** Pre-publication. This repository is private during dissertation
> work and will be released publicly with a Zenodo DOI alongside the published
> Paper III. Please do not redistribute.

## What this is

Research code, configuration, and validation artifacts for **Paper III** of
the dissertation *"Defensible Intelligent Imaging and Reduction for Scalable
Digital Forensics."*

Paper III extends the SIFTING selective imaging mechanism (Grier & Richard,
DFRWS 2015) with HVEA — the High-Value Evidence Area dependency framework
established in Paper II — as the reasoning layer that drives acquisition
decisions, prioritizes artifact layers by forensic value, and provides
explainable reasoning for what is acquired, deferred, or omitted.

The contribution is not the mechanism. SIFTING is the proven base. The
contribution is the HVEA-driven reasoning layer that replaces SIFTING's
static investigator-defined relevance assumption with a dependency-aware,
explainable, defensibility-evaluable acquisition framework.

## Companion papers

- **Paper I** — *Intelligent Methods for Digital Forensics: A PRISMA review.*
  Establishes the field-level vocabulary for defensibility (completeness,
  integrity, transparency, explainability, defensibility) that Paper III's
  validation harness operationalizes.
- **Paper II** — *HVEA: A Layered Model for High-Value Evidence Areas in
  Digital Forensics.* Defines the ten artifact layers, four tiers, and
  evidentiary dependencies that Paper III formalizes into an executable
  reasoning graph.

## Repository layout

```
paperiii/
    phase1_hvea_graph/        Formal HVEA dependency graph + reasoner
        hvea_schema.json          JSON Schema for the graph
        hvea_graph_winxp.json     XP variant (Charlie, Jo, Pat)
        hvea_graph_winvista.json  Vista variant (Terry)
        hvea_graph_win11.json     Windows 11 variant (controlled set)
        hvea_reasoner.py          Topological reasoning module
    phase2_sifting_mapping/   HVEA → SIFTING acquisition profile
        sifting_profile_mapper.py
    phase3_acquisition/       HVEA-enhanced SIFTING acquisition harness
        acquisition_harness.py
    phase4_validation/        Phase 5 empirical validation harness
        validation_harness.py
    docs/
        M57_Win11_Pilot_Protocol.md   Step-by-step per-image protocol
    README.md                 Scaffolding-level documentation

runs/                         Per-image run outputs (mostly gitignored)
    <image-id>_hvea/
        defensibility_report.json     ← tracked
        validation_report.json        ← tracked
        partial_image/                ← gitignored (evidence)
        acquisition_trace.jsonl       ← gitignored (volume)
    <image-id>_baseline/
        baseline_manifest.json        ← tracked

hashes/                       Source-image SHA-256 (chain of custody)
logs/                         Per-image logs (gitignored; .gitkeep retained)
```

## What is and isn't in git

**Tracked.** All code, all HVEA graphs, the protocol, README files, and the
small structured reports each run produces — `defensibility_report.json`,
`validation_report.json`, `baseline_manifest.json`. Source-image SHA-256
hashes (small, important for chain of custody).

**Not tracked.** Evidence images (`*.E01`, `*.dd`), baseline DFXML
inventories (regenerable, 50–500 MB each), partial-image trees produced by
acquisition (could be tens of GB across all eight subjects), and per-run
reasoning / acquisition trace JSONL files (volume — Charlie's reasoning
trace alone is ~40k records). These are documented in `.gitignore` with
inline justification.

The exclusions are forensic-specific: the M57 dataset is publicly available
so the data isn't sensitive, but the *derived artifacts* are voluminous,
and bloating the repo with binary-ish data would degrade it permanently.
Evidence stays in the local workspace; the repo holds the means to
reconstruct it.

## Datasets

- **M57-Patents** (Charlie, Jo, Pat, Terry × two captures each) — Windows XP
  SP3 and Vista Business SP2 images from the M57 scenario.
- **W11_HVEA_14D** — controlled Windows 11 image, 14-day activity protocol
  (see Paper II Section 4.2).

Eight M57 images + one Win11 image = nine images total. The M57 dataset is
[publicly distributed](https://digitalcorpora.org/corpora/scenarios/m57-patents/).
The Win11 image is a controlled experimental capture described in Paper II.

## Reproducing the pipeline

The end-to-end per-image workflow is in
`paperiii/docs/M57_Win11_Pilot_Protocol.md`. Briefly: hash and mount the
image, generate a fiwalk DFXML inventory, run Phase 1 to produce
dependency-ordered acquisition targets, Phase 2 to translate them into a
SIFTING-compatible profile, Phase 3 to execute the acquisition, and Phase
5 (`phase4_validation/`) to compute the eight measurement-framework
metrics.

```bash
# After cloning, with E01 images in place under ~/selective-imaging/images/:
export PROJ=~/selective-imaging
export PIII=$(pwd)/paperiii
export IMG="charlie-2009-12-11"
export GRAPH="$PIII/phase1_hvea_graph/hvea_graph_winxp.json"
# Then follow paperiii/docs/M57_Win11_Pilot_Protocol.md from step 1.
```

## Citation

(Placeholder — will be replaced with DOI and BibTeX entry at publication.)

> Author, O. (forthcoming). *HVEA-Enhanced SIFTING: A Mechanism-Bound
> Selective Imaging Framework Grounded in Evidentiary Dependency Reasoning.*

## License

This repository is private and unlicensed during dissertation work. A
permissive open-source license (likely MIT for code, CC-BY-4.0 for
documents) will be applied at publication.

## Acknowledgements

Built on prior work by Grier & Richard (SIFTING, DFRWS 2015) and Garfinkel
(DFXML, M57-Patents corpus). The HVEA framework was developed under the
supervision of Dr. C. Varol.
