# Source-preserving boundary grafting and bounded hole recovery for ScrollFiesta

Status: local submission draft, not submitted or published. Prepared October 28, 2026. This software contribution is separate from the ongoing PHerc0813 First Letters investigation.

## Submission summary

We developed and locally evaluated two closely related experimental improvements on public ScrollFiesta, pinned revision `bce8a65f97652316efb084171a17d2f1f8d3ae1a`: recovery of compatible source faces otherwise lost during component filtering, and bounded hole recovery that avoids a reproduced duplicate-triangle failure. The contribution targets surface preservation and geometric correctness. It does not claim newly recovered ancient text, anatomical identity, whole-scroll reconstruction or worldwide novelty.

## 1. Boundary Grafting v2

Small components could still lose useful source triangles after the existing coverage protection, while attaching each component wholesale could introduce incompatible faces. The graft uses original shared edges to attach compatible subsets to retained neighboring owners. Owner selection is deterministic, considers multiple retained neighbors, and rechecks recorded incompatibilities against current assignments. Vertices are not moved and new triangles are not invented by this stage. Incomplete conflict-pair collection disables recovery rather than treating a truncated list as complete.

The full-pipeline +32Y experiment recovered 27 source faces. Its measured maximum loss at 427 boundary probes fell from approximately 1.312 to 0.760 voxels. Annotated proximity coverage increased from 2,237 to 2,241 unique voxels under the recorded sampling/radius protocol. This coverage includes more than one annotation ID and is not an anatomical-identity certificate. The v2 experiment retained one pre-existing hole-fill conflict, explicitly reported rather than attributed to grafting or hidden.

Other recorded cases recover 16 faces in the original development crop and 13 in another cube's central window; the +32X regression is byte-identical. These are limited local comparisons, not a broad benchmark across scrolls.

Evidence: `scrollfiesta-comparison/BOUNDARY_GRAFT_REPORT.md`, `boundary-graft-results.json`, `boundary-graft-v2.patch`, `boundary-graft-sha256.txt`, the production-helper controls and independent geometric audits.

## 2. Hole Recovery v5

The reproduced hole-fill failure introduced the same geometric triangle with opposite orientations. After the duplicate correction, the conservative v4 control left a 19-vertex hole open. The opt-in v5 experiment searches a bounded set of complete triangulations of that cycle. It adds no Steiner vertices, retains source geometry, and preserves boundary, orientation, angular-fan and intersection filters. Failure or budget exhaustion rejects the proposal atomically.

On the saved +32Y case, v5 retains all 5,139 v4 source faces, retains four other valid fill faces, and recovers 17 faces inside the target cycle: 5,143 to 5,160 final faces. Native conflicts, final duplicates and degenerates are zero. Annotated proximity coverage increases from 2,239 to 2,241. The recorded 427-probe boundary maximum remains approximately 0.759852 voxels. These figures must not be added to the graft's counts as though they shared the same immediate baseline.

An independent rational audit checks all 267 overlapping-AABB new/source and new/new candidate pairs, with zero forbidden intersections. It does not independently recertify all source/source pairs; the native audit covers the complete mesh. The full-input run retains the recorded source geometry and matches the separately audited saved recovery geometrically. Regression and halo results remain part of the evidence.

Evidence: `scrollfiesta-comparison/hole-recovery-v5/FULL_RECOVERY_REPORT.md`, `SAVED_RECOVERY_REPORT.md`, `full-evaluation-01/metrics.json`, `saved-evaluation-02/metrics.json`, `replay-certificate.json`, regression records and the case evidence manifest. Earlier Spanish reports are immutable historical evidence; this draft provides an English account without rewriting them.

## Reproducibility and integration scope

The experimental base is ScrollFiesta, with its attribution and licenses preserved. These are local modifications on that pinned revision, not a claim of upstream inclusion or compatibility with the latest upstream. The graft patch is incremental and depends on the earlier split-ownership coverage work; it is not a standalone patch for an arbitrary checkout. Hole recovery includes production source changes and its search helper; publishing only a report or the graft patch would be insufficient.

Existing build/run/evaluation scripts and unique command receipts preserve inputs, environment, source/binary hashes, controls, successful outputs and rejected attempts. Computational work ran sequentially with CPUQuota 25%, Nice 19, IOWeight 10, MemoryMax 384 MiB, no swap, inaccessible GPU devices, one numerical thread and a desktop reserve of at least 3,072 MiB. Existing results should be reused; clean-checkout reproduction, if needed, must use fresh directories under the same guard.

## Limitations to disclose

- The measured improvements are local and small; they do not establish fiber continuity or same-sheet identity across a full scroll.
- Cross-core continuity remains separately constrained by calibration and distance gates. No unsupported seam weld should be advertised as solved.
- PHerc0813 continuation and its rejected UV maps are separate research, not proof that these two algorithms recover text.
- No First Letters result is claimed. The software submission should not contain an inferred or forced reading.

## Release work still required

1. Assemble the complete dependency-ordered modifications against the pinned public base, retaining all third-party notices and licenses.
2. Provide concise English build/run instructions, exact public-data identifiers and reproducible before/after examples, including images or mesh views linked to their recorded metrics.
3. Check the exported package in a clean checkout using the required guards, without rerunning unchanged scientific benchmarks unnecessarily. Document latest-upstream compatibility separately if tested.
4. Supply an accessible release/repository URL and complete the official Progress Prize form. This draft is not evidence of an upload or submission.

## Official prize reference

Official rules checked October 28, 2026: https://scrollprize.org/prizes#progress-prizes . The published next monthly deadline is October 31, 2026, 11:59 p.m. Pacific. Progress Prizes consider documented, useful software contributions and reproducible improvements or bug fixes on challenge data. The $20,000 best-submission award is selected by the challenge team; this work has no guaranteed award. First Letters is a separate prize with its own image, mesh, reproducibility and review requirements.
