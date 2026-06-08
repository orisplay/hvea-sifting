# M57 + Win11 Pilot Protocol — Per-Image Acquisition and Validation

Step-by-step protocol for running the Paper III pipeline against the eight
M57 images plus the Windows 11 controlled image. The pilot starts with
Charlie Dec 11 (already partly prepared — DFXML exists) and expands once
the pipeline is verified.

> **Audience.** You at the Kali workstation.
> **Posture.** Every step writes to a log. Every step verifies the previous
> step before proceeding. No silent skips, no implicit assumptions.

---

## 0. Conventions and directory layout

```
~/selective-imaging/
    images/XP_2009/           # original E01 images (source of truth)
        charlie-2009-11-12.E01
        charlie-2009-12-11.E01
        jo-2009-11-20-oldComputer.E01
        jo-2009-12-07-newComputer.E01      (if present; else 'jo-2009-11-20-newComputer.E01')
        pat-2009-11-16.E01
        pat-2009-11-17.E01
        terry-2009-11-12.E01               (Vista — verify name; see step 0.1)
        terry-2009-11-19.E01               (Vista — verify name; see step 0.1)
    images/Win11/
        W11_HVEA_14D.E01 .. W11_HVEA_14D.E18   (single 18-segment image)
    mounts/                   # one mount point per image (read-only)
        charlie-2009-12-11-ro/
        ...
    dfxml/                    # baseline inventories
        charlie-2009-12-11.dfxml
        ...
    hashes/                   # SHA-256 of every source image
        charlie-2009-12-11.sha256
        ...
    runs/                     # one directory per image per condition
        charlie-2009-12-11_hvea/
        charlie-2009-12-11_baseline/
        ...
    logs/                     # per-image run logs
        environment.log
        charlie-2009-12-11.log
        ...

~/paperiii/                   # scaffolding (extracted from paperiii_scaffolding.zip)
    phase1_hvea_graph/
        hvea_graph_winxp.json     # XP variant — for Charlie, Jo, Pat
        hvea_graph_winvista.json  # Vista variant — for Terry
        hvea_graph_win11.json     # Win11 variant — for W11_HVEA_14D
        hvea_reasoner.py
        ...
    phase2_sifting_mapping/
    phase3_acquisition/
    phase4_validation/
```

### 0.1 Image identifier and OS-variant mapping

Image identifier = the E01 filename without the `.E01` extension. Stored in
`$IMG` per session. The OS variant is fixed per image and selects which
HVEA graph to use:

| Image identifier                            | OS     | HVEA graph              |
| ------------------------------------------- | ------ | ----------------------- |
| charlie-2009-11-12                          | XP SP3 | hvea_graph_winxp.json   |
| charlie-2009-12-11                          | XP SP3 | hvea_graph_winxp.json   |
| jo-2009-11-20-oldComputer                   | XP SP3 | hvea_graph_winxp.json   |
| jo-2009-12-07-newComputer (or Nov 20 new)   | XP SP3 | hvea_graph_winxp.json   |
| pat-2009-11-16                              | XP SP3 | hvea_graph_winxp.json   |
| pat-2009-11-17                              | XP SP3 | hvea_graph_winxp.json   |
| terry-2009-11-12                            | Vista  | hvea_graph_winvista.json|
| terry-2009-11-19                            | Vista  | hvea_graph_winvista.json|
| W11_HVEA_14D                                | Win11  | hvea_graph_win11.json   |

The protocol sets `$GRAPH` automatically based on `$IMG` in step 0.2.

### 0.2 Per-session env vars

Set at the top of every shell session:

```bash
# Workspace root
export PROJ=~/selective-imaging
export PIII=~/paperiii

# The image we're working on (change this per image)
export IMG="charlie-2009-12-11"

# Auto-select the HVEA graph based on the image identifier
case "$IMG" in
    terry-*)               export GRAPH="$PIII/phase1_hvea_graph/hvea_graph_winvista.json" ;;
    W11_HVEA_14D)          export GRAPH="$PIII/phase1_hvea_graph/hvea_graph_win11.json" ;;
    *)                     export GRAPH="$PIII/phase1_hvea_graph/hvea_graph_winxp.json" ;;
esac

# Image source — confirm location matches your layout
export SRC="$PROJ/images/XP_2009/$IMG.E01"
[ "$IMG" = "W11_HVEA_14D" ] && export SRC="$PROJ/images/Win11/$IMG.E01"

echo "IMG=$IMG"
echo "GRAPH=$GRAPH"
echo "SRC=$SRC"
ls -l "$SRC" 2>/dev/null || echo "WARNING: source file not found at $SRC"
```

If the source path doesn't resolve, stop and fix the layout before
proceeding.

### 0.3 Directory bootstrap

Once per workstation:

```bash
mkdir -p "$PROJ"/{mounts,dfxml,hashes,runs,logs}
```

---

## 1. Verify the environment (once per workstation)

```bash
{
    echo "=== Environment Log ==="
    echo "Date: $(date -Iseconds)"
    echo "Host: $(hostname)"
    echo "User: $(whoami)"
    uname -a
    fiwalk -V 2>&1
    ewfmount -V 2>&1 | head -2
    python3 --version
} > "$PROJ/logs/environment.log"

cat "$PROJ/logs/environment.log"
```

Expected: SleuthKit 4.14.0, libewf 20140816, Python 3.x.

---

## 2. Verify and hash the source image

```bash
test -f "$SRC" || { echo "Image not found: $SRC"; return 1; }

sha256sum "$SRC" | tee "$PROJ/hashes/$IMG.sha256"
export IMG_SHA256=$(awk '{print $1}' "$PROJ/hashes/$IMG.sha256")
echo "IMG_SHA256=$IMG_SHA256"
```

---

## 3. Mount the image read-only

```bash
mkdir -p "$PROJ/mounts/${IMG}-ewf" "$PROJ/mounts/${IMG}-ro"

sudo ewfmount "$SRC" "$PROJ/mounts/${IMG}-ewf"
ls -la "$PROJ/mounts/${IMG}-ewf"   # expect: ewf1

sudo mmls "$PROJ/mounts/${IMG}-ewf/ewf1" | tee -a "$PROJ/logs/$IMG.log"
```

Examine the `mmls` output:

- **M57 XP images**: NTFS partition typically starts at sector **63** → offset `63*512=32256`.
- **Vista images (Terry)**: NTFS partition typically starts at sector **2048** → offset `2048*512=1048576`.
- **Win11 (GPT)**: main Windows partition typically starts at sector **444416** → offset `444416*512=227540992`.

Set the offset based on what `mmls` actually showed:

```bash
# Example for an XP image at sector 63 — adjust per the mmls output:
export OFFSET=$((63 * 512))

sudo mount -o ro,loop,offset=$OFFSET,show_sys_files,streams_interface=windows \
    "$PROJ/mounts/${IMG}-ewf/ewf1" \
    "$PROJ/mounts/${IMG}-ro"

ls "$PROJ/mounts/${IMG}-ro" | head -20
```

Expected contents:

- **XP**: `WINDOWS`, `Documents and Settings`, `RECYCLER`, `Program Files`
- **Vista**: `Windows`, `Users`, `$Recycle.Bin`, `Documents and Settings` (compatibility symlink)
- **Win11**: `Windows`, `Users`, `$Recycle.Bin`, `Program Files`, `OneDriveTemp`

If the second mount fails, unmount stage 1 and re-check the offset:

```bash
sudo umount "$PROJ/mounts/${IMG}-ewf"
```

---

## 4. Generate the baseline DFXML inventory

```bash
{
    echo "=== fiwalk run for $IMG ==="
    date -Iseconds
    echo "Source: $SRC"
    echo "Source SHA-256: $IMG_SHA256"
} >> "$PROJ/logs/$IMG.log"

time fiwalk -X "$PROJ/dfxml/$IMG.dfxml" "$SRC" 2>> "$PROJ/logs/$IMG.log"

ls -lh "$PROJ/dfxml/$IMG.dfxml"
grep -c "<fileobject" "$PROJ/dfxml/$IMG.dfxml" | \
    xargs -I N echo "fileobject count: N"
```

Expected:
- **M57 XP**: 10–60 minutes, 30k–80k file objects, DFXML 30–200 MB.
- **Vista (Terry)**: similar — 50k–150k file objects.
- **Win11**: hours to complete, 200k+ file objects, DFXML 500 MB+.

If the file object count is implausibly small (< 1000), the partition
wasn't read. Re-check the offset.

---

## 5. Round-trip — Phase 1 reads the DFXML

```bash
cd "$PIII"

python3 phase1_hvea_graph/hvea_reasoner.py \
    --graph     "$GRAPH" \
    --inventory "$PROJ/dfxml/$IMG.dfxml" \
    --out       "$PROJ/runs/${IMG}_hvea_targets.json" \
    --trace     "$PROJ/runs/${IMG}_hvea_reasoning.jsonl" \
    -v 2>&1 | tee -a "$PROJ/logs/$IMG.log"
```

Sanity checks:

```bash
python3 -c "
import json
ts = json.load(open('$PROJ/runs/${IMG}_hvea_targets.json'))['targets']
print('targets:', len(ts))
from collections import Counter
c = Counter()
for t in ts:
    for l in t['layers']:
        c[l] += 1
print('layers represented (incl. multi-layer):', dict(sorted(c.items())))
missing = set('ABCDEFGHIJ') - set(c.keys())
print('missing layers:', sorted(missing) if missing else 'NONE')
"
```

Expected: hundreds of targets, **all ten layers A–J represented**. Missing
layers indicate the chosen graph's acquisition paths don't match what is
on this image — open `$GRAPH`, find the layer, add or adjust the path
pattern, re-run. Log the change in `$IMG.log` with a one-line rationale.
This is a research finding (path divergence per OS variant), not a bug.

---

## 6. Phase 2 — produce the SIFTING profile

```bash
python3 phase2_sifting_mapping/sifting_profile_mapper.py \
    --targets "$PROJ/runs/${IMG}_hvea_targets.json" \
    --graph   "$GRAPH" \
    --out     "$PROJ/runs/${IMG}_profile.json" \
    -v 2>&1 | tee -a "$PROJ/logs/$IMG.log"
```

Expected: 4 tier groups (I, II, III, IV), criteria count matching Phase 1.

---

## 7. Phase 3 — HVEA-enhanced SIFTING acquisition

```bash
python3 phase3_acquisition/acquisition_harness.py \
    --profile    "$PROJ/runs/${IMG}_profile.json" \
    --mount      "$PROJ/mounts/${IMG}-ro" \
    --out        "$PROJ/runs/${IMG}_hvea" \
    --image-name "$IMG.E01" \
    --image-hash "$IMG_SHA256" \
    -v 2>&1 | tee -a "$PROJ/logs/$IMG.log"
```

Expected: `acquired N`, `not_found M`, `failed 0`. The `not_found` count
on a real image is informative — it indicates HVEA-targeted paths the
specific image doesn't contain (e.g. no Chrome profile on a Firefox-only
system). Logged automatically.

Sanity check:

```bash
ls -la "$PROJ/runs/${IMG}_hvea/defensibility_report.json"
find "$PROJ/runs/${IMG}_hvea/partial_image" -type f | wc -l
du -sh "$PROJ/runs/${IMG}_hvea/partial_image"
```

---

## 8. Full-disk baseline manifest

The full-disk condition uses the mount itself as the ground-truth
reference; we don't duplicate the entire image into a partial_image tree.
We record a baseline manifest to anchor the comparison:

```bash
mkdir -p "$PROJ/runs/${IMG}_baseline"

cat > "$PROJ/runs/${IMG}_baseline/baseline_manifest.json" <<EOF
{
  "report_type": "baseline_manifest",
  "image_name": "$IMG.E01",
  "image_hash": "$IMG_SHA256",
  "mount_point": "$PROJ/mounts/${IMG}-ro",
  "baseline_dfxml": "$PROJ/dfxml/$IMG.dfxml",
  "acquisition_strategy": "full_disk_reference",
  "captured_at": "$(date -Iseconds)"
}
EOF
```

---

## 9. Phase 5 — Validation

```bash
python3 phase4_validation/validation_harness.py \
    --run-dir            "$PROJ/runs/${IMG}_hvea" \
    --baseline-image     "$SRC" \
    --baseline-mount     "$PROJ/mounts/${IMG}-ro" \
    --baseline-inventory "$PROJ/dfxml/$IMG.dfxml" \
    --out                "$PROJ/runs/${IMG}_hvea/validation_report.json" \
    -v 2>&1 | tee -a "$PROJ/logs/$IMG.log"
```

Defensibility will show `n/a` until the rubric is locked with Cihan.

---

## 10. Unmount and archive

```bash
sudo umount "$PROJ/mounts/${IMG}-ro"
sudo umount "$PROJ/mounts/${IMG}-ewf"

{
    echo "=== Run complete for $IMG ==="
    date -Iseconds
    echo "OS variant graph used: $GRAPH"
    echo "Outputs:"
    echo "  DFXML:               $PROJ/dfxml/$IMG.dfxml"
    echo "  HVEA targets:        $PROJ/runs/${IMG}_hvea_targets.json"
    echo "  HVEA profile:        $PROJ/runs/${IMG}_profile.json"
    echo "  HVEA acquisition:    $PROJ/runs/${IMG}_hvea/"
    echo "  Validation report:   $PROJ/runs/${IMG}_hvea/validation_report.json"
} >> "$PROJ/logs/$IMG.log"
```

---

## 11. Pre-flight checklist before the next image

Before changing `$IMG`:

- [ ] Pipeline completed without errors in any phase.
- [ ] Validation report exists and is non-empty.
- [ ] No `failed` decisions in the acquisition trace.
- [ ] All ten HVEA layers (A–J) represented in the reasoning output,
      OR any missing-layer adjustments to the OS variant graph are
      logged and re-runs reflect them.
- [ ] Current image is unmounted; mount points are empty.

Then change `$IMG` (which auto-updates `$GRAPH` and `$SRC` via the case
block in step 0.2) and repeat from step 2.

---

## Pilot execution order

1. **Charlie Dec 11** — XP. DFXML already exists; resume at step 5.
2. **Charlie Nov 12** — XP. Cross-temporal pair with Dec 11; reveals
   HVEA-graph stability across two captures of the same subject.
3. **One Vista image (Terry Nov 12 or 19)** — first Vista run; surfaces
   any Vista-specific path divergences early.
4. **Pat Nov 16** — XP, but a different subject; cross-subject check.
5. Then expand to the remaining four (Jo × 2, Terry's other capture, Pat
   Nov 17) once the pipeline is verified across OS variants.
6. **Win11 (W11_HVEA_14D)** runs last because the image is large and
   fiwalk is slow on it; do it once everything else is stable.

This order is designed so that a graph-path-divergence finding on
Terry's first Vista run doesn't block XP progress — the variants are
independent.

---

## What to bring to the next advisor meeting

After Charlie's two captures plus one Vista image complete:

1. The validation reports for each.
2. The HVEA reasoning traces showing dependency-ordered acquisition for
   each image.
3. Any OS-variant graph adjustments made during the runs, with one-line
   rationale per change. These are findings.
4. The defensibility reports.

---

## Common failure modes and recovery

**fiwalk produces a tiny DFXML or zero fileobjects.**
Partition not read correctly. Re-check `mmls`, confirm offset, retry.

**Mount fails: "wrong fs type, bad option, bad superblock".**
Offset wrong. M57 XP: sector 63. Vista (Terry): 2048. Win11 main: 444416.

**Phase 1 returns zero acquired across all layers.**
Almost always the wrong graph for the image. Confirm `$GRAPH` matches
the OS. Check sample DFXML `<filename>` entries against the graph's
acquisition paths.

**Phase 1 missing a layer (e.g. no Layer F).**
The OS variant's browser paths don't match what's on this specific
image (e.g. user never installed any browser). Spot-check by listing
the expected directory under the mount. If it genuinely doesn't exist,
that's a finding — log it and move on. If it exists at a different
path, extend the graph.

**Phase 3 reports many `not_found`.**
Expected. HVEA paths are exhaustive; specific images only contain a
subset. Spot-check a few `not_found` entries against the mount to
confirm the path really is absent.

**Validation shows `integrity: fail`.**
Acquisition copy mismatch. Should never happen on a clean read-only
mount. Check the `mismatches` detail in the validation report.

---

This protocol is rigid by design. The OS-variant graph selection in step
0.2 is the most important change from the earlier draft — running an XP
image through the Win11 graph (or vice versa) will produce a misleading
"pipeline failure" that's really a paths mismatch. The case block prevents
that mistake structurally.
