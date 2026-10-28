# Papyrus Atlas

*Surface Reconstruction and Ancient Text Research*

**Papyrus Atlas** is an independent effort to reconstruct carbonized Herculaneum papyrus surfaces and recover verifiable ancient text. The project connects source-preserving geometry research with surface support, CT registration and ink-reading experiments.

The current standalone software milestone is the two geometry algorithms below. Separate reading research has completed a public-detector CPU baseline; verifying a full word, demonstrating ink benefit on our repaired surface, resolving core continuity and obtaining enough PHerc0813 reader context remain active or future milestones. No newly deciphered text is claimed.

See [Project milestones](PROJECT_MILESTONES.md) for completed results, open problems and the path toward independently verifiable letters, a word and a short line. The [challenge guide](CHALLENGE_SUBMISSION.md) explains the broader purpose while keeping the current contribution focused on the two verified methods.

## Paris4 coordinate audit

A new [source-axis audit](research/paris4-coordinate-audit/README.md) corrects the NRRD-to-atlas index convention using independently reproduced same-scan CT anchors. The corrected query removes the earlier high-score ink candidate; full modern registration and ink/letter benefit remain unvalidated. Geometry and all previous releases are unchanged.

## Measured before/after geometry

![Before/after boundary grafting and whole-cycle hole recovery on the Paris4 case](figures/before-after.png)

The upper row compares the historical source before/after grafting (5,112 to 5,139 faces); orange marks the 27 recovered original faces. The lower row compares conservative hole filling with complete recovery (5,143 to 5,160 faces); green marks the 17 added faces. The saved meshes share camera and coordinates within each row. This is a preserved historical pipeline figure: the standalone graft replays its actual graph inputs, and standalone hole recovery reproduces the reference oriented geometry. It does not show ink, fibers or independently certified anatomical continuity. [Figure/input hashes](figures/provenance.json).

| Standalone check | Observed result | Scope |
| --- | --- | --- |
| Real graft graph replay | 27 recoveries; all reference labels match | Supplied graph constraints, not CT segmentation |
| Whole-cycle recovery | 5,143 retained faces + 17 additions = 5,160 | One length-19 Paris4 cycle |
| Final exact added-face audit | 267 overlapping-AABB pairs; 0 forbidden contacts | New/source and new/new only |
| Isolated verification | 8 automated tests pass | Original lab inaccessible; site packages disabled |

See [submission readiness](SUBMISSION_READINESS.md) for the official-requirement review and scientific limitations, and [English historical context](HISTORICAL_CONTEXT_EN.md) for the wider reading effort. The [current review edition](https://github.com/danielcadev/papyrus-atlas/releases/tag/papyrus-atlas-review-v1) provides one entry point for code, documents and the figure.

## Standalone software

An independent mesh-stage research project with two deterministic surface recovery methods. **Execution requires Python 3.10+ and its standard library only.** No ScrollFiesta checkout, native library, compiler, NumPy, Triangle, Clipper2, GCO, trained model, API, network access or GPU is required.

The project has its own importable package and command-line interface. It accepts triangular meshes in JSON and plain Wavefront OBJ; a strict import-only adapter supports historical VESMESH1 fixtures. It refuses UV-bearing historical files rather than silently dropping their UV coordinates.

## Methods

- **Boundary grafting:** compatible original faces attach to retained owners through original shared-edge adjacency. Retained owners do not merge or move. Complete conflict constraints are an explicit input, not an assumed geometry certificate. Final assignments are committed atomically after all recorded constraints pass.
- **Whole-cycle hole recovery:** a bounded search triangulates an isolated 3–19 vertex source boundary without moving vertices, welding, discarding source triangles or adding Steiner vertices. New/source and new/new contacts are checked with exact rational arithmetic, including shared-point cases. Source diagonals, boundary orientation, degeneracy, shape and necessary angle-fan bounds remain admission controls. Failure or exhaustion commits no patch.

This independent Python implementation descends from experiments on public ScrollFiesta. Runtime independence does **not** mean independent historical origin or worldwide novelty. Attribution and MIT notices remain in ATTRIBUTION.md and LICENSES/. Historical results and their original interpretation remain preserved separately.

## Run

There is no installation or build step. From this project directory:

```bash
python3 -m vesuvius_surface --help
python3 -m vesuvius_surface graft tests/fixtures/graft-input.json /tmp/graft-result.json
python3 -m vesuvius_surface recover tests/fixtures/paris4-source.json tests/fixtures/paris4-cycle.json /tmp/recovered.obj --report /tmp/recovery-report.json
```

Use unique output filenames: existing results are never overwritten. The API is `Mesh`, `boundary_graft` and `recover_cycle`; see the modules and tests for examples. For experiments in the lab, use the unchanged resource guard as shown in REPRODUCE.md instead of launching unrestricted computation.

## Verified scope

The exported historical real-data graft graph reproduces all 27 assignments exactly. The independent hole stage fills the Paris4 cycle with 17 faces, retaining 5,143 source faces and reaching 5,160. Its oriented geometry matches the historical v5 output, with zero forbidden contacts in the 267 final overlapping-AABB new-face pairs. See VERIFICATION.md for the exact run and limitations.

The supplied graph and mesh fixtures originate from public PHercParis4 / Scroll 1 data processed during earlier experiments. This is a standalone **mesh-processing project**, not a standalone CT-to-text system: it does not extract or segment CT, infer fibers, flatten meshes or detect ink. Its graft API consumes supplied complete adjacency/conflict evidence; it does not yet generate that evidence from CT or detect arbitrary projected chart conflicts. The exact checker does not recertify unchanged source/source pairs. Angle bounds are necessary conditions, not a full UV certificate. No anatomical identity, new letters, whole-scroll continuity, current-upstream superiority or prize is claimed.

## Historical evidence

The original sealed software package, archive checksum, upstream-derived snapshots, failures and comparisons are retained unchanged in the lab and in the preserved legacy release. PROVENANCE.json records source and fixture hashes. The standalone project does not load that archive. The repository is public for software review. No challenge application has been submitted. The current standalone contribution is linked in CHALLENGE_SUBMISSION.md; earlier access states remain preserved in historical records.

Historical documents record earlier project names and access states. The current project name is Papyrus Atlas, the repository is public, and no challenge application has been submitted. Original-language evidence remains unchanged; all current reviewer-facing text is English.

Latest CT-only follow-up: [exterior registration evidence](research/paris4-exterior-registration/README.md). Registration remains rejected at the unchanged 0.1 margin; no verified ink or letters.

[Spatial control follow-up](research/paris4-independent-controls/README.md): cold-start fits and new reserved CT targets still reject registration; original geometry and the 0.1 minimum remain unchanged.
