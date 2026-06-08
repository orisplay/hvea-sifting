# Repository setup — one-time instructions

Set up the Paper III repository on GitHub (private), initialize it locally
in your `~/selective-imaging/` workspace, and make the first commit.
Follow once. Total time: about 15 minutes.

---

## 1. Create the private GitHub repository (browser)

1. Sign in to GitHub.
2. Top right → "+" → **New repository**.
3. Settings:
   - **Repository name**: `paperiii-hvea-sifting` (or `dissertation-paper3`, your call)
   - **Description**: *"HVEA-enhanced SIFTING: mechanism-bound selective imaging. Pre-publication research code."*
   - **Visibility**: **Private** (critical — do not pick Public)
   - **Initialize this repository with**: leave ALL three boxes unchecked
     (no README, no .gitignore, no license — you're bringing your own)
4. Click **Create repository**.

You'll land on an empty repo page with a "Quick setup" block. Note the
SSH URL — it looks like `git@github.com:<yourusername>/paperiii-hvea-sifting.git`.

---

## 2. Configure git on Kali (once per workstation)

```bash
# Identity
git config --global user.name  "Your Name"
git config --global user.email "you@university.edu"

# Sensible defaults
git config --global init.defaultBranch main
git config --global pull.rebase false
```

If you haven't set up SSH access to GitHub yet:

```bash
# Generate a key (skip the next two lines if you already have ~/.ssh/id_ed25519)
ssh-keygen -t ed25519 -C "you@university.edu"
cat ~/.ssh/id_ed25519.pub
```

Copy the printed public key, paste it into GitHub → Settings → SSH and GPG
keys → New SSH key. Then test:

```bash
ssh -T git@github.com
# Expect: "Hi <yourusername>! You've successfully authenticated, but GitHub does not provide shell access."
```

If SSH is too much friction right now, you can use HTTPS with a personal
access token instead — but SSH is one-time setup and pays back forever.

---

## 3. Choose your repository root layout

This is a real design decision and matters. Two reasonable options:

**Option A — Repo IS the working directory.**
`~/selective-imaging/` becomes the git repo. The `paperiii/` scaffolding
directory sits inside it alongside `runs/`, `logs/`, `hashes/`, etc. The
`.gitignore` keeps E01s and DFXML out.

Pros: one root, simplest mental model, runs/ outputs naturally tracked.
Cons: `~/selective-imaging/` already contains Paper II artifacts
(`Win11_HVEA/`, `XP_HVEA/`, `policy0_xp_core/`, etc.) — you'd be putting
Paper II content under Paper III's repo. Could be intentional ("the whole
dissertation in one repo") or could be confusing.

**Option B — Repo is just the scaffolding and outputs.**
Create `~/paperiii-repo/` as the git root, containing the `paperiii/`
scaffolding plus `runs/`, `logs/`, `hashes/`. Keep `~/selective-imaging/`
as the *evidence and Paper II workspace*. Configure the protocol to
write Phase 3/5 outputs into the repo's `runs/` directory.

Pros: clean separation; Paper III repo doesn't accidentally absorb Paper
II content.
Cons: two directory trees to think about; the protocol's `$PROJ` variable
needs to change.

**Recommendation: Option B.** Cleaner narrative for the published repo,
and your Paper II content stays unentangled. The instructions below
follow Option B.

---

## 4. Initialize the local repo

```bash
# Pick a path that is not ~/selective-imaging/ (per Option B above)
mkdir -p ~/paperiii-repo
cd ~/paperiii-repo

# Copy the scaffolding into the repo
cp -r ~/paperiii ./paperiii

# Drop in the three repo-level files (from this setup bundle)
cp /path/to/.gitignore     .gitignore
cp /path/to/README.md      README.md
cp /path/to/COMMITS.md     COMMITS.md

# Create the directories that need to exist but stay empty until you run
mkdir -p runs hashes logs
touch runs/.gitkeep hashes/.gitkeep logs/.gitkeep

# Initialize git
git init
git branch -M main

# Verify .gitignore is doing the right thing BEFORE the first commit
git add -A
git status
```

Look at `git status`. You should see:

- `.gitignore`, `README.md`, `COMMITS.md` staged
- The entire `paperiii/` tree staged (code + graphs + protocol)
- `runs/.gitkeep`, `hashes/.gitkeep`, `logs/.gitkeep` staged
- **No** `.E01`, `.dfxml`, `partial_image/`, or `_hvea_targets.json` files

If anything large or evidence-bearing shows up in the staged list, STOP
and fix `.gitignore` before committing. It's much harder to remove a
mistakenly-committed evidence file from history later than to prevent it.

---

## 5. First commit and push

```bash
git commit -m "repo: initial scaffolding for Paper III

Phase 1 HVEA dependency graph and reasoner, Phase 2 SIFTING profile
mapper, Phase 3 acquisition harness, Phase 5 validation harness, and
the M57+Win11 per-image pilot protocol. Three OS-variant HVEA graphs
(XP, Vista, Windows 11), each populated from Paper II investigation
findings.

End-to-end pipeline smoke-tested on synthetic inventories. First
real-evidence Phase 1 + Phase 2 run against Charlie Dec 11 produced
3,604 acquisition targets across all 10 HVEA layers."

# Link to GitHub
git remote add origin git@github.com:<yourusername>/paperiii-hvea-sifting.git

# Push
git push -u origin main
```

You should see GitHub accept the push and the repository on GitHub now
shows the scaffolding.

---

## 6. Tag the initial state

```bash
git tag -a v0.1-scaffolding -m "Initial scaffolding, pre-pilot.

Three OS-variant HVEA graphs populated from Paper II investigations.
All four phases (1, 2, 3, 5) smoke-tested end-to-end on synthetic data.
Phase 1+2 validated against Charlie Dec 11 real evidence; Phase 3+5
not yet run against real evidence."

git push origin v0.1-scaffolding
```

The tag becomes a permanent marker for "this is what existed before any
real-evidence runs." Useful when you write the methods section and want
to cite the exact state of the code at a moment in time.

---

## 7. Bring forward what you've already produced

You generated three Charlie Dec 11 artifacts earlier today that live in
`~/selective-imaging/runs/`. Two of them (`_hvea_targets.json`,
`_hvea_reasoning.jsonl`) are correctly gitignored — they're voluminous
and regenerable. But it's worth recording that this run happened. Two
options:

**Option A — Add a brief run-log entry.** Create a markdown file in the
repo documenting the run, then commit it:

```bash
cat > ~/paperiii-repo/runs/charlie-2009-12-11_summary.md <<'EOF'
# Charlie Dec 11 — first real-evidence Phase 1+2 run

Date: 2026-06-07 (evening)
Image: charlie-2009-12-11.E01 (M57-Patents)
Image SHA-256: <fill in from ~/selective-imaging/hashes/>
OS variant graph: hvea_graph_winxp.json

## Phase 1 (HVEA reasoning)
- Inventory items (fiwalk): 40,065
- Acquired (HVEA targets): 3,604
- Multi-layer (also_serves): 694
- Omitted: 36,384
- Selectivity: ~9% of inventory acquired

## Phase 1 layer coverage
A: 2, B: 7, C: 730, D: 1, E: 157, F: 2691, G: 615, H: 4, I: 1, J: 1
All ten layers represented. No graph adjustments required.

## Phase 2 (SIFTING profile)
- Groups: 4 (one per HVEA tier)
- Tier I  (A, B):           9 criteria, no deps
- Tier II (C):             730 criteria, deps [B]
- Tier III (E, F, G):    2,859 criteria, deps [B, C]
- Tier IV (H, I, J):         6 criteria, deps [B, C, D, E, G]

## Notes
- Layer F dominance (2,691) reflects Charlie Dec 11's heavy USPTO/WIPO
  browsing session documented in Paper II investigation notes.
- $MFT and $UsnJrnl surfaced as filesystem-structure targets (Phase 1
  structural-pattern emission worked as designed).
- No path-format mismatches between fiwalk DFXML and XP graph patterns.

## Status
Phase 3 (acquisition) and Phase 5 (validation) not yet executed.
EOF

cd ~/paperiii-repo
git add runs/charlie-2009-12-11_summary.md
git commit -m "phase1: record first real-evidence Phase 1+2 run on Charlie Dec 11

40,065 inventory items, 3,604 HVEA-selected acquisitions, all ten
layers represented. No XP-graph adjustments required on first run."
git push
```

**Option B — defer the summary until Phase 3+5 complete tomorrow** and
write a single richer summary then. Either works.

---

## 8. Daily workflow afterward

```bash
# Start of session
cd ~/paperiii-repo
git status
git pull        # only matters if you also work from a second machine

# ...do work; run pipeline; observe; possibly edit a graph...

# End of session
git status
git add -A
git diff --staged   # check what's about to be committed
git commit -m "<scope>: <descriptive message — see COMMITS.md>"
git push
```

That's it. The repo is now your research log.

---

## When the paper is accepted

1. Decide on a license (recommended: MIT for code, CC-BY-4.0 for docs).
2. Add `LICENSE` and `LICENSE-docs` files; commit.
3. Flip repo to Public via GitHub Settings.
4. Tag a release (`v1.0-paper`) matching the published version.
5. Archive the release on [Zenodo](https://zenodo.org/) (automatic via the
   GitHub integration) to get a DOI you can cite in the paper.
6. Add the DOI badge to the README.

That's the publication flow. Don't worry about it now.
