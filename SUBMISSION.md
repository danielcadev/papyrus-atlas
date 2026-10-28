# Progress Prize contribution: source-preserving boundary grafting and hole recovery

Prepared for the October 2026 Progress Prizes. This package is ready for review and upload after its verification record and archive checksums have been attached; it is not itself a submitted application or an awarded prize.

Official form: https://docs.google.com/forms/d/e/1FAIpQLSc4flEfgK2nyjoczz2_U_XrIGMlgrnSknWatLqrFPnbtKfZwg/viewform

Rules: https://scrollprize.org/prizes#progress-prizes . Checked October 28, 2026. The published monthly deadline is October 31, 2026, 11:59 p.m. Pacific. These two changes are bundled because they address closely coupled surface-loss and hole-fill failures in the same experimental pipeline.

## Contribution description for the form

We contribute two locally validated, source-preserving improvements to public ScrollFiesta (base revision bce8a65f97652316efb084171a17d2f1f8d3ae1a), with dependency-ordered patches, portable reproduction tooling, before/after geometry and complete relevant historical evidence.

(1) **Data.** The principal case is public PHercParis4 / Scroll 1 CT cube 01744_02256_04048 from the harmonized manual-instance-label collection. We use a predeclared +32Y window with Otsu surface input; manual labels enter only post-hoc evaluation. Additional recorded crop regressions and halo checks are included, with their original scope. We do not claim a new-scroll or anatomically independent holdout.

(2) **Why this helps reading.** Useful surface triangles can be lost when small components are filtered, while naive attachment or hole filling can create invalid geometry. Keeping compatible existing surface and rejecting incompatible additions gives later flattening and ink detection more usable geometric input. Our contribution improves those prerequisites; it does not claim that added area already contains verified letters.

(3) **What becomes possible in the tested case.** Boundary Grafting v2 deterministically attaches compatible source faces to retained neighbors through original edges, recovering 27 source faces in the principal window without moving vertices or merging owners. The separately measured boundary-probe maximum improves from about 1.312 to 0.760 voxels. Hole Recovery v5 replaces a rejected duplicate-producing greedy proposal with a bounded search over complete triangulations of the same 19-vertex cycle. It retains all 5,139 source faces and four other valid fills, adding the missing 17 faces: 5,143 to 5,160 final faces, with no final geometric duplicates or degenerates in the checked case. It preserves existing filters and rejects atomically on failure or exhausted budgets.

(4) **Evidence.** The package contains real meshes, before/after figures, input/source/output hashes, control and regression reports, exact quarter-voxel fidelity evidence with its stated scope, failed attempts and source snapshots. A clean upstream extraction, patch application, cold single-job build and full real-data pipeline replay reproduce both changes. The final v5 file is byte-identical to the saved result. The independent rational new/source and new/new audit checks 267 overlapping-AABB pairs with zero forbidden contacts. The complete native audit has zero conflicts on the saved identical geometry, but retains its shared-point blind spots; this is not a full exact source/source certificate.

The changes are opt-in and preserve source geometry and the existing experimental safeguards. The code and demonstration use triangular meshes in ScrollFiesta's existing pipeline, without changing its public API or asserting VC3D integration. We include exact pinned-source reproduction rather than claiming latest-upstream compatibility.

## Information the submitter supplies

- Full name and email.
- Individual/team description; if a team, identify the human team leader.
- Optional Discord display name.
- An accessible URL for this contribution/release (the form requires a URL).
- Acceptance of the official terms by the submitter.

No identity, team membership, public release URL or agreement is fabricated. Uploading this archive and submitting the form remain separate actions. The package contains no newly discovered text; First Letters remains a separate future objective.

## Limits to retain when submitting

Local improvements do not prove same-sheet identity, fibers, full-scroll continuity, new ancient text, universal superiority or worldwide novelty. Core-weld calibration remains an independent unresolved issue. PHerc0813 width-extension results are outside these two software claims. More details are in RESULTS.md, ATTRIBUTION.md and the preserved reports.

AI assistants helped develop and check the implementation. The submitted algorithms are deterministic computational geometry, not a newly discovered AI-laboratory model. No model weights, training service or private laboratory results are needed to reproduce them.
