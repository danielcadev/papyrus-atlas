# Vesuvius Surface Recovery: Progress Prize review guide

This contribution consists of **two mesh-processing algorithms**, their reusable standard-library Python implementation, relevant fixtures, tests, reproduction instructions and evidence. It does not submit the entire lab research history as additional achievements. The preserved older ScrollFiesta-based experiments establish provenance and comparison; they are not a runtime dependency of the standalone implementation.

Repository: https://github.com/danielcadev/vesuvius-boundary-grafting-hole-recovery

The standalone version is on branch `standalone-v1`. The previous version remains on `main` and at tag `software-progress-2026-10-v1`, including its private legacy release assets. The repository remains **private**. A URL to a private repository does not give challenge reviewers access; do not submit this as a publicly accessible contribution unless access/publication is arranged with the owner. No publication, invitation, terms acceptance or form submission is authorized by this document.

## Files for the standalone contribution

- `vesuvius-surface-recovery-standalone-v1.tar.gz`: independent source project, fixtures, relevant verification records and attribution; no native upstream implementation or binary.
- `vesuvius-surface-recovery-standalone-v1.tar.gz.sha256`: archive integrity checksum.
- This English guide: contribution scope and form-ready text.

Archive SHA256: `33924cf942b38665b0aaed6886dcc6dc67bb63be9b2ed9f673863f1bcaa35a10`.

The 118MB legacy archive is retained separately as historical evidence; it is not the standalone software or an installation prerequisite. All other lab research remains preserved locally; no new claims about PHerc0813 letters, fibers, UV-width extension or core continuity are included in this two-algorithm submission.

## Reproduction instructions for reviewers

Extract the standalone archive and read `README.md`, `REPRODUCE.md`, `VERIFICATION.md`, `ATTRIBUTION.md` and `PROVENANCE.json`. No installation/build/download is needed for the library or CLI; Python 3.10+ standard library is sufficient. The optional guarded experiment runner requires Linux user systemd.

From the extracted `vesuvius-surface-recovery` directory:

```bash
bash tools/run_guarded.sh review-UNIQUE 180 python3 -I -S "$PWD/tools/verify_project.py" /tmp/surface-review-UNIQUE
```

Choose a new job name and output directory. The tool refuses to overwrite results. This verifies controls, fixture integrity, the actual graft graph replay, independent hole triangulation, source preservation and exact added-face contacts.

Measured standalone results: eight controls pass; 27 graft assignments match the actual historical graph export; a 19-vertex source boundary receives 17 faces, retaining 5,143 source faces and all source coordinates; final count 5,160; final exact audit checks 267 overlapping-AABB new/source and new/new pairs with zero forbidden contacts. Oriented output geometry matches the historical v5 reference. The isolated run passed with the entire original lab directory inaccessible and Python site packages disabled.

## Form fields

Use the submitter's actual name, email and optional Discord display name. The submitter should verify these directly in the form. Do not invent human collaborators.

### Team description

```text
I am submitting as an individual independent researcher under the project name Vesuvius Lab / Vesuvius Surface Recovery. Codex AI assistants helped with implementation, debugging, verification and documentation; they are not human team members. The standalone Python tool has no ScrollFiesta runtime or build dependency. Its historical algorithm lineage, fixtures and relevant MIT attribution are preserved.
```

Use this individual wording only if there are no other human contributors who should be named.

### Contribution URL

After reviewer access or a separately authorized publication decision, use the standalone branch/release URL. Do not describe a private URL as publicly accessible. Keep the URL field blank while the contribution is intentionally private and not ready to submit.

### What is your contribution?

```text
Vesuvius Surface Recovery provides two independently executable mesh-processing algorithms: boundary grafting and bounded whole-cycle hole recovery. The Python implementation requires only its standard library, with no ScrollFiesta checkout, compilation, native dependencies, trained model or external API. The methods descend from attributed experiments on public ScrollFiesta; execution independence is not a claim of independent invention.

(1) Data. Validation uses preserved graph and triangular-mesh fixtures from public PHercParis4 / Scroll 1 CT cube 01744_02256_04048, originating in the earlier fixed +32Y Otsu experiment. The graph was exported from the actual historical graft call. The hole cycle is selected from the conservative source mesh alone. These are historical same-scroll fixtures, not new CT reconstructions or an independent-scroll holdout.

(2) Relevance to reading. Compatible source faces can be discarded by component filtering, and rejected or invalid hole fills can leave useful surfaces incomplete. These methods preserve more geometric input for downstream flattening and ink detection. A downstream increase in letter recovery has not been measured.

(3) Demonstrated behavior. Boundary grafting attaches compatible original faces to retained owners through original-edge adjacency without merging retained owners or changing geometry. The standalone implementation reproduces the historical graph's 27 recoveries exactly. It requires supplied complete graph constraints and does not yet generate a CT or projected-chart conflict graph. Whole-cycle recovery independently triangulates a 19-vertex boundary, retaining all 5,143 indexed source faces and source coordinates and adding 17 faces to reach 5,160. It uses exact rational new-contact checks, source-diagonal exclusion, boundary orientation, degeneracy/shape controls and necessary angle-fan bounds. Refusal or exhausted budgets commits no partial patch. JSON and plain triangular OBJ are supported.

(4) Evidence. Eight controls and a real mesh-stage replay pass from a fresh project copy with the entire original lab directory inaccessible and Python site packages disabled. The resulting oriented geometry matches historical v5. The final exact new/source and new/new audit checks 267 overlapping-AABB pairs with zero forbidden contacts. Source/fixture hashes, implementation, instructions, verification records, failed attempts and license notices are provided; the complete legacy evidence archive remains separately preserved.

This is a two-algorithm mesh-processing contribution, not a CT-to-text pipeline. It does not provide CT segmentation, flattening, fibers, anatomical identity, a full UV certificate, a source/source exact audit, new letters, worldwide novelty or current-upstream superiority. No new model or private AI-laboratory discovery is needed to reproduce it.
```

### Terms / Send

The owner must review current terms and make the submission decision. This guide and uploading to the private repository do not submit an application. No prize or eligibility determination is asserted.
