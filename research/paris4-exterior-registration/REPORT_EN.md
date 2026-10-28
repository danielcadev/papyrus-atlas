# Paris4 exterior CT registration follow-up

Registration remains rejected. The minimum raw-CT Pearson of 0.6 and margin of 0.1 over the same six four-voxel shift controls were preserved. No fitted transform was admitted, no geometry or UV was changed, and no ink or letter recovery is demonstrated.

## Experiments

The verified native-NRRD-to-old-volume ZYX convention and catalogue affine were retained. Both valid trials reuse the SHA-pinned 88³ matched-footprint grid and fit only CT outside the repaired 32³ ROI plus its four-voxel exclusion band. Residual translation is bounded to ±4 old voxels and each linear residual entry to ±0.01. Each fit is capped at 2,048 evaluations and 120 seconds. The parameters are frozen before raw ROI validation. Validation samples modern CT directly with the same 64-midpoint voxel footprint and six original shift controls.

| Trial | Fit samples / reserved exterior samples | Raw validation Pearson | Best shifted control | Margin | Decision |
| --- | ---: | ---: | ---: | ---: | --- |
| Closer exterior collar, intensity objective | 8,195 / 8,194 | 0.8578014078 | 0.7664491471 | 0.0913522607 | Reject |
| Exterior central differences, support corrected | 7,564 / 7,564 | 0.8580502838 | 0.7661695976 | 0.0918806862 | Reject |

Both valid fits converge inside their parameter bounds: 455 and 546 evaluations. The collar's reserved intensity correlation is 0.9060905 versus 0.9056019 at its initial transform. The corrected gradient fit's reserved gradient correlation is 0.6720256 versus 0.6702205 initially. These are different objectives and must not be compared as if both measured raw intensity similarity. Reserved points are withheld from this final optimizer call only. The reused prior corner-block initializer already used some of their CT values, and interleaved gradient stencils share source voxels. Thus these metrics are neither end-to-end unseen nor independent generalization evidence. For example, reserved center (100,132,154) and its six gradient endpoints belong to a prior training block. The frozen plans' statement "never used by optimizer" is qualified by this provenance correction; those originals are preserved. [Independent review](INDEPENDENT_REVIEW_EN.md) records the issue. The repaired ROI has been inspected in previous work and is not an untouched holdout. This follow-up is exploratory, with fixed per-fit plans, not a preregistered blind evaluation.

The prior valid corner-block affine remains the best recorded valid margin, 0.0916497, until the corrected gradient trial improves that diagnostic slightly to 0.0918807. This small change does not meet 0.1 and does not demonstrate an anatomical improvement or a measured registration error bound. The limiting control is still the +4 native-Z shift. Old-CT self-correlation has a diagnostic margin of 0.1478457 against the same shifts; this neither establishes attainability across scans nor replaces the admission gate.

## Preserved invalid attempt

`paris4-exterior-gradient-v1` is INVALID for the intended exclusion protocol. Although its centers lie outside the exclusion band, some central-difference endpoints enter that band. The first independent verifier detects this and exits with an assertion failure. Its source, plan, fit, raw output and failure logs are preserved. Its margin of 0.0920043 is not counted as a valid result. A new trial expands center exclusion by one voxel and passes the complete endpoint-support check. No old outputs were edited or overwritten.

## Verification and limits

The independent lab verifier checks input hashes, training/reserved disjointness and derivative support, both fitting objectives, all raw validation correlations and unchanged gates. The exclusion check concerns old/native derivative support, not a certified swept-support band in the moving modern CT. It recomputes eight direct 64-midpoint CT footprints from observed scan bytes across the two valid trials. All 120 files of the preceding sealed coordinate-audit phase remain byte-identical. No missing CT is replaced by fill values. Runtime guards retain CPUQuota=25%, Nice=19, IOWeight=10, MemoryMax=384MiB, no swap, GPU inaccessible, all five numerical thread limits at one and at least 3,072MiB available desktop reserve. Fit process peaks are below 133MiB child RSS; each run has its resource receipt.

`replay_saved_controls.py` offers a small offline standard-library replay of the saved raw CT correlations and gate decisions. It does not reproduce optimization, source sampling, anatomical correspondence or ink. The lab source snapshots need the existing lab data layout, NumPy and SciPy. Source object references, hashes and license information remain in the preceding coordinate audit. The published 3D ink field is not used in any fit, and no new score projection is admitted.

A useful next investigation needs independent exterior CT landmarks or a physically supported deformation model with reserved spatial blocks. Repeating affine optimizations or selecting parameters to cross the inspected ROI threshold would not supply that evidence. None of these rejected transforms is suitable for claiming recovered text.

Only a local evidence commit is authorized here. No push, application edit or submission is performed.
