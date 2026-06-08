# Commit conventions for this repository

This is a research repository, not a software product. Commits should be
readable as **a research log**, not as a feature changelog. The point of the
discipline is that twelve months from now, when you're writing the
dissertation defense, you can reconstruct what changed in the HVEA graph,
when, and *why*.

## Shape of a good commit message

```
<scope>: <one-line summary in present tense, lowercase, no period>

<empty line>

<body: what changed, and — more importantly — what observation prompted it.
If the change is in response to a real-image run, name the image and the
layer or finding that surfaced the change. Wrap at ~72 columns.>
```

`<scope>` is one of: `phase1`, `phase2`, `phase3`, `phase5`, `graph-xp`,
`graph-vista`, `graph-win11`, `protocol`, `docs`, `repo`.

## Examples

Good — the message explains a finding:

```
graph-xp: add /WINDOWS/Prefetch path variant for Charlie Nov 12

Charlie Nov 12 run surfaced 4 Prefetch files under /Windows/Prefetch/
(capitalized 'Windows', not 'WINDOWS') because fiwalk preserves the
on-disk casing and Charlie's earlier capture had a case-variant
directory entry. Layer E coverage was 0 before this; 36 entries after.
This is consistent with Paper II's note on case-sensitivity divergence
across captures. Logged as a finding in the run log.
```

Good — straightforward code change:

```
phase1: fix structural-pattern emission when inventory lacks $MFT entry

Some DFXML emitters skip $MFT and $UsnJrnl as filesystem-structure
artifacts. The reasoner was silently dropping Layers I and J in that
case. Now emits them as direct-acquisition targets when not present in
the inventory, with a rationale annotation.
```

Bad — uninformative:

```
fix bug
```

```
update graph
```

```
WIP
```

## When the message names a finding, also log it

Graph changes that respond to a real-image observation should ALSO be
recorded in the per-image log (`~/selective-imaging/logs/<image>.log`)
with a one-line rationale. Two records of the same finding — git commit
and image log — make the change auditable from either direction.

## Tags

Tag every "I just generated artifacts I'm bringing to the advisor" state
with `meeting-YYYY-MM-DD` so you can return to it. Tag every paper-ready
state with `paper-draft-vN`.

## Force-push policy

Do not force-push to `main`. Use feature branches for any rewriting; merge
when clean. The history of *when* things changed is itself defensibility
evidence.
