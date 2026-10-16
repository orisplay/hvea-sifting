# Paper III — HVEA-SIFTING Pipeline Scaffolding

End-to-end scaffolding for HVEA-SIFTING. Four phases, each a runnable module
that consumes the previous phase's output and produces inputs the next phase
needs.

> **Status.** This is research scaffolding, not production tooling. Each phase
> is intentionally small, self-contained, and command-line driven so each can
> be inspected, criticized, and revised independently.

## Pipeline at a glance

```
                               +-------------------+
  Paper II's HVEA model -----> | Phase 1: graph    |  (formal dependency graph)
                               +-------------------+
                                        |
                  baseline DFXML -----> + (HVEA reasoner)
                                        |
                                        v
                               +-------------------+
                               | Phase 2: mapping  |  (SIFTING profile)
                               +-------------------+
                                        |
                                        v
                               +-------------------+
              mounted image -> | Phase 3: harness  |  (partial image + reports)
                               +-------------------+
                                        |
                                        v
                               +-------------------+
   baseline + ground truth --> | Phase 4: validate |  (eight-metric report)
                               +-------------------+
```

Explainability and defensibility are not a separate pipeline stage: every
acquisition decision produces a reasoning trace in Phase 3, and every run
produces a validation and defensibility report in Phase 4 — both
automatically, not retrofitted.

## Phase 1 — HVEA dependency formalization

Path: `phase1_hvea_graph/`

| File | What it is |
| --- | --- |
| `hvea_schema.json` | JSON Schema describing the HVEA graph format. |
| `hvea_graph_winxp.json` | XP variant (Charlie, Jo, Pat). |
| `hvea_graph_winvista.json` | Vista variant (Terry). |
| `hvea_graph_win11.json` | Windows 11 variant (controlled set). |
| `hvea_reasoner.py` | Loads a graph, takes a baseline file inventory (DFXML or JSONL), and produces a dependency-respecting ordered acquisition target list and the reasoning trace (Eq. 1). |

Each graph populates four tiers, ten layers A-J, and the interpretive
dependencies grounded in Paper II's tables. Select the graph that matches the
image's operating system.

Run against a real baseline DFXML (XP example):

```bash
python phase1_hvea_graph/hvea_reasoner.py \
    --graph     phase1_hvea_graph/hvea_graph_winxp.json \
    --inventory <fiwalk_output>.dfxml \
    --out       phase1_hvea_graph/targets.json \
    --trace     phase1_hvea_graph/reasoning_trace.jsonl
```

## Phase 2 — HVEA-to-SIFTING profile mapping

Path: `phase2_sifting_mapping/`

| File | What it is |
| --- | --- |
| `sifting_profile_mapper.py` | Translates Phase 1's target list into a SIFTING-compatible acquisition profile with criteria grouped by HVEA tier, each criterion carrying its HVEA grounding for the explainability metric. |

Run:

```bash
python phase2_sifting_mapping/sifting_profile_mapper.py \
    --targets phase1_hvea_graph/targets.json \
    --graph   phase1_hvea_graph/hvea_graph_winxp.json \
    --out     phase2_sifting_mapping/sifting_profile.json
```

## Phase 3 — Dependency-ordered acquisition

Path: `phase3_acquisition/`

| File | What it is |
| --- | --- |
| `acquisition_harness.py` | Executes the Phase 2 profile against a mounted disk image, producing a partial image organized by tier and layer, an acquisition trace with per-decision HVEA grounding, and a defensibility report. |

Run against a read-only mounted image:

```bash
python phase3_acquisition/acquisition_harness.py \
    --profile    phase2_sifting_mapping/sifting_profile.json \
    --mount      /mnt/charlie_nov_ro \
    --out        runs/charlie_nov_hvea \
    --image-name charlie_nov.E01 \
    --image-hash <sha256_of_image>
```

Output structure:

```
runs/charlie_nov_hvea/
    partial_image/
        tier_I/A/Windows/System32/config/SYSTEM
        tier_I/B/Windows/System32/config/SAM
        tier_II/C/Users/alice/Documents/...
        tier_III/E/Windows/Prefetch/...
        tier_IV/H/Windows/System32/winevt/Logs/...
    acquisition_trace.jsonl
    acquisition_profile.json
    defensibility_report.json
```

## Phase 4 — Empirical validation

Path: `phase4_validation/`

| File | What it is |
| --- | --- |
| `validation_harness.py` | Compares a Phase 3 run against the full-disk baseline along the eight metrics (acquisition speed, storage reduction, artifact preservation, completeness, integrity, transparency, explainability, defensibility). |

Run:

```bash
python phase4_validation/validation_harness.py \
    --run-dir            runs/charlie_nov_hvea \
    --baseline-image     /evidence/charlie_nov.E01 \
    --baseline-mount     /mnt/charlie_nov_full_ro \
    --baseline-inventory /evidence/charlie_nov_baseline.dfxml \
    --out                runs/charlie_nov_hvea/validation_report.json
```

The defensibility metric returns `n/a` until a pre-registered rubric is
supplied via `--rubric`; this is intentional and tracks the open question
documented in the manuscript's limitations.

## Running the full pipeline on one image (M57 example)

```bash
# 0. Acquire a verified read-only mount of the source image, e.g.:
#    sudo ewfmount charlie_nov.E01 /mnt/charlie_nov_ewf
#    sudo mount -o ro,loop,offset=$((63*512)) \
#         /mnt/charlie_nov_ewf/ewf1 /mnt/charlie_nov_ro

# 1. Baseline inventory via fiwalk (full disk ground truth).
fiwalk -X charlie_nov_baseline.dfxml /mnt/charlie_nov_ro

# 2. HVEA reasoning pass (select the graph for the image's OS).
python phase1_hvea_graph/hvea_reasoner.py \
    --graph phase1_hvea_graph/hvea_graph_winxp.json \
    --inventory charlie_nov_baseline.dfxml \
    --out phase1_hvea_graph/charlie_nov_targets.json \
    --trace phase1_hvea_graph/charlie_nov_reasoning.jsonl

# 3. Profile mapping.
python phase2_sifting_mapping/sifting_profile_mapper.py \
    --targets phase1_hvea_graph/charlie_nov_targets.json \
    --graph phase1_hvea_graph/hvea_graph_winxp.json \
    --out phase2_sifting_mapping/charlie_nov_profile.json

# 4. Acquisition.
python phase3_acquisition/acquisition_harness.py \
    --profile phase2_sifting_mapping/charlie_nov_profile.json \
    --mount /mnt/charlie_nov_ro \
    --out runs/charlie_nov_hvea \
    --image-name charlie_nov.E01 \
    --image-hash <sha256>

# 5. Validation against full-disk baseline.
python phase4_validation/validation_harness.py \
    --run-dir runs/charlie_nov_hvea \
    --baseline-image charlie_nov.E01 \
    --baseline-mount /mnt/charlie_nov_ro \
    --baseline-inventory charlie_nov_baseline.dfxml \
    --out runs/charlie_nov_hvea/validation_report.json
```

Repeat for each M57 subject (Charlie, Jo, Pat, Terry x two capture dates) and
for the Windows 11 image. The per-image protocol with environment setup,
mount offsets, and sanity checks is in `docs/M57_Win11_Pilot_Protocol.md`.

## Conventions

- All paths in profiles and traces use forward slashes and a leading slash.
- All hashes are SHA-256.
- All times are UTC ISO-8601.
- JSONL is used for streaming traces; JSON for structured documents.
- Every output file is human-readable enough that a reviewer can audit a
  run without running the code.
