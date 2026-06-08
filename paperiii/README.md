# Paper III — Mechanism-Bound Selective Imaging

End-to-end scaffolding for HVEA-extended SIFTING. Four phases, each a runnable
module that consumes the previous phase's output and produces inputs the next
phase needs.

> **Status.** This is research scaffolding, not production tooling. Each phase
> is intentionally small, self-contained, and command-line driven so each can
> be inspected, criticized, and revised independently before Paper III's
> empirical runs commit to anything.

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
   baseline + ground truth --> | Phase 5: validate |  (metrics report)
                               +-------------------+
```

Phase 4 (explainability and defensibility) is woven into Phases 3 and 5
rather than being its own pipeline stage: every acquisition decision produces
a reasoning trace, and every run produces a defensibility report — both
automatically, not retrofitted.

## Phase 1 — HVEA dependency formalization

Path: `phase1_hvea_graph/`

| File | What it is |
| --- | --- |
| `hvea_schema.json` | JSON Schema describing the HVEA graph format. |
| `hvea_graph.json`  | The populated graph: four tiers, ten layers A–J, sixteen interpretive dependencies, two convergence patterns, all grounded in Paper II's Tables 2 and 3. |
| `hvea_reasoner.py` | Loads the graph, takes a baseline file inventory (DFXML or JSONL), produces a dependency-respecting ordered acquisition target list and the reasoning trace. |
| `test_inventory.jsonl` | Synthetic inventory used to smoke-test the reasoner. |

Run against your real baseline DFXML:

```bash
python phase1_hvea_graph/hvea_reasoner.py \
    --graph     phase1_hvea_graph/hvea_graph.json \
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
    --graph   phase1_hvea_graph/hvea_graph.json \
    --out     phase2_sifting_mapping/sifting_profile.json
```

## Phase 3 — HVEA-enhanced SIFTING acquisition

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

## Phase 5 — Empirical validation

Path: `phase4_validation/`

| File | What it is |
| --- | --- |
| `validation_harness.py` | Compares a Phase 3 run against the full-disk baseline along the eight metrics from the experimental design doc (acquisition speed, storage reduction, artifact preservation, completeness, integrity, transparency, explainability, defensibility). |

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
flagged in the experimental design document (section 7).

## Running the full pipeline on one image (M57 example)

```bash
# 0. Acquire a verified read-only mount of the source image, e.g.:
#    sudo ewfmount charlie_nov.E01 /mnt/charlie_nov_ewf
#    sudo mount -o ro,loop,offset=$((63*512)) \
#         /mnt/charlie_nov_ewf/ewf1 /mnt/charlie_nov_ro

# 1. Baseline inventory via fiwalk (full disk ground truth).
fiwalk -X charlie_nov_baseline.dfxml /mnt/charlie_nov_ro

# 2. HVEA reasoning pass.
python phase1_hvea_graph/hvea_reasoner.py \
    --graph phase1_hvea_graph/hvea_graph.json \
    --inventory charlie_nov_baseline.dfxml \
    --out phase1_hvea_graph/charlie_nov_targets.json \
    --trace phase1_hvea_graph/charlie_nov_reasoning.jsonl

# 3. Profile mapping.
python phase2_sifting_mapping/sifting_profile_mapper.py \
    --targets phase1_hvea_graph/charlie_nov_targets.json \
    --graph phase1_hvea_graph/hvea_graph.json \
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

Repeat for each M57 subject (Charlie, Jo, Pat, Terry × two capture dates) and
for the Windows 11 image set.

## What is deliberately *not* in this scaffolding

A few things are out of scope on purpose. Each maps to an open question in
the experimental design document:

- **Defensibility scoring rubric.** Stubbed; awaits the advisor lock.
- **Research-question-anchored hypotheses and thresholds.** The validation
  harness reports values; turning values into pass/fail against research
  hypotheses happens after RQs are locked.
- **Standard-SIFTING-without-HVEA condition.** The harness supports it
  trivially (different profile, same execution), but Phase 5 will not
  generate that condition until the third-condition question is resolved.
- **Repeated runs / variance characterization.** Single per-image runs
  for now; loop driver is straightforward when needed.

## Conventions

- All paths in profiles and traces use forward slashes and a leading slash.
- All hashes are SHA-256.
- All times are UTC ISO-8601.
- JSONL is used for streaming traces; JSON for structured documents.
- Every output file is human-readable enough that a reviewer can audit a
  run without running the code.
