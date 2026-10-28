# Paris4 coordinate correction and ink-benefit audit

## Outcome

**A coordinate-convention error was identified and corrected. Recovery of real ink or letters is still not demonstrated.** The native index axes in this particular NRRD cube match canonical old-volume **ZYX**, despite the historical `triangles-source-xyz.npy` filename. The earlier ink bridge incorrectly interpreted these native indices as catalogue XYZ coordinates.

A fresh, standard-library-only replay downloaded SHA-pinned public NRRD and same-scan CT objects and tested all 48 signed local axis conventions. The selected convention has no permutation or flips when mapping native NRRD indices to canonical ZYX. Its reserved-plane correlation is **0.9990509125230466**, with margin **0.649692740107969** over the other conventions. The former reverse-axis interpretation has only approximately 0.371 correlation in the initial all-anchor check. No ink, expected letter or modern-score outcome was used to select this correction.

Correcting the coordinates removes the earlier high-score candidate on the added faces. The corrected graft additions contribute 89 additional queried field positions, with raw scores **1–13**, rather than the earlier 96 positions and maximum 204. There are **zero** additional positions with score >=128. The hole additions contribute 160 positions with scores **1–2**. These are third-party prediction scores, not calibrated probabilities or independent ink truth.

The modern cross-scan diagnostic improves substantially but **still fails** the unchanged control margin. No fitted residual transform is admitted. The source meshes, UV maps, recovered faces, exact contact results and immutable old reports remain unchanged. The current geometry-algorithm results are independent of this CT-query correction.

## Coordinate equation

Let `n` be a native NRRD index triplet and `O = [1744, 2256, 4048]` the named cube origin in canonical ZYX. The validated old-volume coordinate passed to the catalogue XYZ affine is:

```text
old_xyz = reverse(n + O)
modern_xyz = A * old_xyz + t
```

The previous query used `n + reverse(O)`, which reverses the origin but fails to reverse the local indices. The array filename containing `xyz` was not an independently verified axis declaration. The initial synthetic sampler and frozen-parent checks verified internal consistency only; they did not establish the external atlas convention.

Historical VMESH coordinates remain in their retained experimental frame. Their vertices are not rewritten. For a retained mesh point `w` in that frame, the historical extraction gives `n = reverse(w - O)`. Therefore the corrected physical old XYZ coordinate is `reverse(O) + (w - O)`. This preserves all stored geometry while correcting queries to external CT/score fields. Do not assume this cube-specific empirical convention for an unrelated NRRD without an anchor check.

Active lab projector and CT-check sources now perform the reversal at the catalogue boundary. Their frozen earlier source snapshots, outputs and hashes remain intact.

## Same-scan test and rejected alternatives

The initial diagnostic examined both named-origin ZYX and header-origin XYZ interpretations, at offsets 0, +/-7, +/-111 and +/-118 in Z. The offsets were motivated by differing recorded volume lengths (14,376, 14,369 and 14,258), not by ink scores. None established an offset correction. The subsequent signed-axis experiment tests the local index convention at the fixed named origin, using 4,096 stride-four samples. Alternating first-axis sample planes select the convention; the other planes validate it. These interleaved planes are a local same-scan check, not an independent-scroll holdout.

The same-scan candidate criteria were fixed before evaluating the signed-axis variants: validation Pearson >=0.95 and margin >=0.1. The chosen convention passes. The portable implementation uses byte offsets in the original Fortran-order NRRD and C-order Zarr chunks, independently of NumPy or the original project loader. Network replay passed with Python site packages disabled in 5.21 seconds, maximum child RSS 44.32 MiB.

## Cross-scan validation remains closed

The original modern CT queries already contain the corrected nominal voxel footprints because the X/Z bounds and quadrature sets are symmetric. Reindexing that array by transposing axes 0 and 2 recovers the corrected queries exactly. An independent verifier also directly recomputes four 64-midpoint cell footprints from observed modern CT bytes, rather than relying only on this transpose.

The registration gate remains Pearson >=0.6 **and** margin >=0.1 over six +/-4-old-voxel controls. The exterior fit excludes the repaired ROI and a four-voxel guard band. It uses no ink and freezes its parameters before validation. The ROI was inspected previously and is not a new unseen holdout.

| Trial | ROI Pearson | Best control | Margin | Gate |
| --- | ---: | ---: | ---: | --- |
| Previous incorrect-axis nominal footprint | 0.617110 | 0.605313 | 0.011797 | Rejected |
| Corrected axes, nominal catalogue affine | 0.842303 | 0.782628 | 0.059675 | Rejected |
| Corrected axes, exterior CT translation | 0.857559 | 0.767081 | 0.090479 | Rejected |
| Corrected axes, footprint-matched exterior residual affine | 0.858298 | 0.766648 | 0.091650 | Rejected |

The translation is `[0.75, 0.5, -0.5]` native voxels. The footprint-matched affine fit uses the same 64 cell midpoints in fitting and validation, with trilinear interpolation of an integer footprint grid for fitting only. Its 445 evaluations converge inside predeclared translation +/-4 and residual-entry +/-0.01 bounds; the residual determinant is 0.9993155. Convergence and improved correlation do not waive the failed margin. The fitted transforms remain rejected proposals. Anatomical registration error remains unmeasured.

## Corrected before/after prediction coverage

The comparison applies the corrected axes and the **nominal** catalogue affine; none of the rejected residual fits is chosen to improve ink. Every retained and added face is included. The same equal-area midpoint quadrature and on-surface nearest-score protocol are used before/after. All retained-face geometry, point queries and values are bit-identical across each ablation.

| Ablation | Faces before -> after | Unique queried positions before -> after | Additional positions | Additional raw range | Additional scores >=128 |
| --- | --- | --- | ---: | --- | ---: |
| Boundary Grafting | 5,112 -> 5,139 | 16,918 -> 17,007 | 89 | 1–13 | 0 |
| Hole Recovery | 5,143 -> 5,160 | 17,018 -> 17,178 | 160 | 1–2 | 0 |

The area-weighted on-surface means for added faces are 3.080013 for grafting and 1.202309 for the hole. The physical added areas remain 0.000341902895821 mm² and 0.001362358366967 mm². All integer score thresholds are saved; threshold 128 is only a reporting point and never a confirmed-ink label. Nearest quantization and finite quadrature influence these counts, which are not exact continuous surface coverage or independent ink observations.

Earlier incorrect-axis score statistics and figures are **superseded for physical association**, not deleted. In particular, the previous 26 added positions with raw score >=128 do not substantiate ink rescue. The corrected weak scores also do not prove the physical absence of ink, given model and remaining registration uncertainty. No letters are inferred in either direction.

## Verification and preservation

Independent verification replayed the portable axis result, all CT control correlations and unchanged gate decisions, four direct canonical CT footprints, the coordinate transform for every corrected triangle, every on-surface score query and the unique additional query indices. Both before/after comparisons retain the previous meshes exactly. All 79 files of the preceding phase were verified unchanged.

Every scientific run retained CPUQuota=25%, Nice=19, IOWeight=10, MemoryMax=384 MiB, no swap, inaccessible GPU devices, five numerical thread limits of one and desktop reserve >=3072 MiB. No application was closed and no registration, geometry or resource threshold was lowered. The longest new job was the footprint-grid fit at 57.60 seconds with maximum child RSS 205.11 MiB.

The fresh same-scan portable replay is independently usable without NumPy, native binaries or the lab checkout; public objects are SHA-pinned and downloaded, not vendored. Advanced CT-fit and score experiments are preserved as lab-source snapshots with their dependency/layout requirements; they are not claimed to be independently runnable through the geometry package alone.

## Application scope

The two geometry algorithms remain a reproducible software contribution. This audit supplies a real coordinate correction and a negative ink-benefit finding, not the missing proof of readable text. No submission was edited or sent, and no new publication was performed. A local commit records the reviewable correction and its evidence; updating an application must retain the failed registration and lack of rescued letters. A duplicate application claiming recovered ink is not warranted.

The next scientific requirement is a defensible registration with independent local structural correspondences or an error bound around the repaired faces, followed by a controlled ink/reading experiment on genuinely sufficient context. The current tiny repaired region is still below the 2D reader's physical-context requirement.
