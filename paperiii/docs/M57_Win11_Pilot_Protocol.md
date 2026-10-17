# Reproducing the HVEA-SIFTING Pipeline — Per-Image Workflow

End-to-end steps to run HVEA-SIFTING against a single Windows disk image and
validate the result. Assumes a Linux environment with The Sleuth Kit
(`fiwalk`, `mmls`), libewf (`ewfmount`), and Python 3.

## 1. Mount the source image read-only

Identify the Windows partition offset from the partition table (`mmls`) before
mounting. The Windows volume begins at:

| OS | Partition scheme | Start sector | Byte offset |
|---|---|---|---|
| Windows XP | MBR | 63 | 32,256 |
| Windows Vista | MBR | 2,048 | 1,048,576 |
| Windows 11 | GPT | 444,416 | 227,540,992 |

```bash
sudo ewfmount image.E01 /mnt/ewf
sudo mount -o ro,loop,offset=<start_sector*512>,show_sys_files,streams_interface=windows \
    /mnt/ewf/ewf1 /mnt/ro
```

## 2. Generate the baseline inventory

```bash
fiwalk -X baseline.dfxml /mnt/ro
```

## 3. Phase 1 — HVEA reasoning

Select the graph that matches the image's operating system
(`hvea_graph_winxp.json`, `hvea_graph_winvista.json`, or
`hvea_graph_win11.json`). The trace records an explicit acquire/omit decision
for every inventory entry.

```bash
python3 phase1_hvea_graph/hvea_reasoner.py \
    --graph     phase1_hvea_graph/hvea_graph_winxp.json \
    --inventory baseline.dfxml \
    --out       targets.json \
    --trace     reasoning_trace.jsonl
```

## 4. Phase 2 — SIFTING profile

```bash
python3 phase2_sifting_mapping/sifting_profile_mapper.py \
    --targets targets.json \
    --graph   phase1_hvea_graph/hvea_graph_winxp.json \
    --out     profile.json
```

## 5. Phase 3 — Acquisition

Produces the partial image (organized by tier and layer), an acquisition
trace, and a defensibility report.

```bash
python3 phase3_acquisition/acquisition_harness.py \
    --profile    profile.json \
    --mount      /mnt/ro \
    --out        run_hvea \
    --image-name image.E01 \
    --image-hash <sha256_of_image>
```

## 6. Phase 4 — Validation

Reports the eight evidentiary-quality metrics. Defensibility returns `n/a`
unless a pre-registered rubric is supplied; in this study it was assessed
qualitatively through independent expert review.

```bash
python3 phase4_validation/validation_harness.py \
    --run-dir            run_hvea \
    --baseline-image     image.E01 \
    --baseline-mount     /mnt/ro \
    --baseline-inventory baseline.dfxml \
    --out                run_hvea/validation_report.json
```

## Negative-space audit

Classify the omitted set directly from the Phase 1 reasoning trace:

```bash
python3 audit/classify_omitted.py reasoning_trace.jsonl residue.txt
```

Repeat per image, selecting the OS-matched graph each time.
