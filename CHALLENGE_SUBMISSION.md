# Vesuvius Surface Recovery — Standalone Boundary Grafting and Hole Recovery

## Project purpose

Vesuvius Lab aims to reconstruct surfaces from carbonized Herculaneum papyri and progress toward verifiable ancient text. Our work spans source-preserving geometry, surface support, flattening/registration experiments and a reproducible public ink-detection baseline. The current standalone deliverable is the geometry layer: two reusable algorithms developed to prevent useful surface from being discarded or filled with invalid geometry.

This Progress Prize contribution is the two algorithms with their code, controls and evidence. The broader project and its milestones explain why they matter; completed technical baselines, unresolved integration and future reading goals are distinguished in `PROJECT_MILESTONES.md`.

Repository: https://github.com/danielcadev/vesuvius-boundary-grafting-hole-recovery/tree/standalone-v1

Standalone release: https://github.com/danielcadev/vesuvius-boundary-grafting-hole-recovery/releases/tag/surface-recovery-standalone-v1

The repository is now public for reviewer access at the owner's explicit request. The form remains an unsubmitted draft. The public standalone branch and release URLs above are the contribution links; accepting terms and submitting remain separate decisions.

## What to provide

- The sealed standalone source archive and checksum, already attached to the standalone release.
- Its relevant supplementary evidence archive and checksum.
- This English contribution guide and `PROJECT_MILESTONES.md` for project context.

The earlier 118MB ScrollFiesta-based package remains separately preserved as historical comparison and provenance. It is not a runtime dependency of the standalone geometry code. Other research is documented as context with its actual status, rather than added to the algorithm submission as unverified achievements.

## Reproduce the algorithm milestone

Read `README.md`, `REPRODUCE.md`, `VERIFICATION.md`, `ATTRIBUTION.md` and `PROVENANCE.json`. Python 3.10+ standard library is sufficient; the optional Linux resource wrapper requires a user systemd session. From the extracted standalone project directory:

```bash
bash tools/run_guarded.sh review-UNIQUE 180 python3 -I -S "$PWD/tools/verify_project.py" /tmp/surface-review-UNIQUE
```

Use new job/output names. The recorded eight controls, 27 graft assignments, 17-face hole recovery and final 267-pair exact audit are already verified. This documentation update does not change or rerun those experiments.

## Team description for the form

```text
I am submitting as an individual independent researcher under the project name Vesuvius Lab. Our long-term objective is to reconstruct carbonized papyrus surfaces and recover verifiable ancient text. Vesuvius Surface Recovery is the current standalone software deliverable. Codex AI assistants helped with implementation, debugging, verification and documentation; they are not human team members. Historical algorithm lineage and relevant attribution are preserved.
```

If other people contributed, name them and their roles instead of using the individual wording. The human submitter supplies/verifies personal details and accepts terms only by their own decision.

## Contribution description for the form

```text
Vesuvius Lab is working toward reconstructing carbonized Herculaneum papyrus surfaces and recovering verifiable ancient text. Vesuvius Surface Recovery is our current independently executable geometry deliverable: boundary grafting and bounded whole-cycle hole recovery. Both run with Python's standard library, without downloading, compiling or loading ScrollFiesta or its native dependencies. Historical algorithm and fixture attribution is retained.

(1) Data. The software is validated using preserved graph and triangular-mesh fixtures from public PHercParis4 / Scroll 1 CT cube 01744_02256_04048, originating in the earlier fixed +32Y Otsu experiment. Graph input was exported from the actual historical graft call; the hole cycle is selected from the conservative source mesh alone. These are same-scroll development fixtures, not an independent-scroll holdout.

(2) Relevance to reading. Our reading experiments exposed the need to preserve useful source surface before flattening and CT sampling. Component filtering can discard compatible triangles, while invalid hole filling can obstruct usable geometry. These two algorithms address those concrete failures. The longer-term goal is to demonstrate preserved or recovered ink strokes on our own repaired surfaces; that downstream reading benefit has not yet been established.

(3) Completed software milestones. The standalone graft reproduces all 27 recoveries from the real exported graph, without merging retained owners or modifying geometry. It requires supplied complete adjacency/conflict constraints. Whole-cycle recovery independently adds 17 triangles to a 19-vertex boundary, retaining all 5,143 indexed source faces and all source coordinates, reaching 5,160 faces. It uses bounded search, exact rational new-contact checks, source-diagonal exclusion, boundary orientation, degeneracy/shape controls and necessary angle-fan bounds. Failures or exhausted budgets commit no partial fill. JSON and plain triangular OBJ are supported.

(4) Evidence and broader project progress. Eight controls and a real mesh-stage replay pass with the entire original lab directory inaccessible and Python site packages disabled. The resulting oriented geometry matches historical v5. The final exact new/source and new/new audit checks 267 overlapping-AABB pairs with zero forbidden contacts. Code, fixtures, hashes, instructions, failed attempts, logs and licenses are preserved.

Separately, we completed a 341-patch CPU reproduction of a public ink detector on a published Paris4 surface and an assisted comparison with a known Greek reference word. The segment overlaps the model's published training data, letters remain ambiguous, and no independently verified new word is claimed. PHerc0813 surface extension has reached 48,597 accepted experimental faces, but the certified square at the recorded center is 0.759246 mm versus 1.2288 mm needed by the reader. Anatomical registration, wider support and core continuity remain open milestones. These experiments explain the project's direction; they are not additional standalone runtime modules or claimed reading breakthroughs.

Our next milestones are to establish supported surface/CT correspondence, demonstrate before/after ink benefit, and then produce independently verifiable letters, a word and a short line. Ten legible letters on a previously unread target are a future ambition. The current submission is the two verified geometry methods, with no claim of new text, complete anatomical/UV certification, unchanged source/source contact freedom, worldwide novelty or current-upstream superiority.
```

## Submission state

Use the public standalone branch and release URLs above in the contribution URL field. This guide and public access do not submit the application, promise qualification or guarantee an award. Original sealed source and evidence assets remain unchanged. The earlier English guide is retained as a previous documentation edition.
