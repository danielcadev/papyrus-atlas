# Paris4 spatial controls and cold-start registration

**Registration remains rejected.** Two fresh fits start from the published catalogue affine with exactly zero residual parameters. Neither uses the earlier optimized initializers. No source geometry, UV or recovered face is modified. No ink scores, letters or text are used, and no ink benefit or anatomical registration error bound is demonstrated.

## Fixed design and independence

Five exterior training blocks contain 10,240 old/native CT target samples. Each trial uses 2,048 newly withheld targets in a separate block with native Z 88:96. ReserveA is Y 148:164, X 116:132; reserveB is Y 176:192, X 116:132. Plans are written before intensities are loaded. All local diagnostics and the global fit use training only. Global parameters are frozen before querying that trial's reserved targets and the original repaired ROI. Trial2 is an exploratory follow-up after trial1, not a blind preregistered study. The original ROI is previously inspected.

The controls are disjoint from each current fit's training, with conservative support proofs covering all allowed translations, linear residuals, cache interpolation, quadrature and observed modern CT interpolation. They are not manually annotated anatomical control points or statistically independent scans. Previous nominal cache generation already sampled modern intensities, but did not optimize on these reserved old/native target values. The original source guard inequality is qualified by a stronger continuous-support check in the independent verification; see [review](INDEPENDENT_REVIEW_EN.md).

Residual translations are bounded to ±2 old voxels and each residual linear entry to ±0.01. These are not enlarged after failure. The original admission thresholds remain raw Pearson>=0.6 and margin>=0.1 over the same six ±4-old-voxel controls, plus converged fitting without a parameter-boundary solution. This phase strengthens admission by also requiring the new reserved block to pass; it never substitutes the reserve for the original ROI gate.

## Results

| Fit and evaluation | Raw CT Pearson | Margin over strongest shifted control | Decision |
| --- | ---: | ---: | --- |
| Trial1 pooled-intensity affine, fresh reserveA | 0.7149906564 | -0.0200862357 | Reject |
| Trial1, original repaired ROI | 0.8441047337 | 0.0792836814 | Reject |
| Trial2 equal mean of five block NCCs, fresh reserveB | 0.0691782566 | -0.0617534169 | Reject |
| Trial2, original repaired ROI | 0.8345949231 | 0.0694520082 | Reject |
| Trial2, previously inspected reserveA, later diagnostic | 0.6921345062 | -0.0344331939 | Reject |

Both optimizations converge but reach an existing linear-parameter boundary: 918 and 943 evaluations against a 2,048-evaluation/120-second cap. Thus neither is admissible even before considering its failed raw validation gate. The second training objective is the arithmetic mean of within-block correlations, not a pooled Pearson. All five blocks remain included. ReserveB has lower measured intensity variation (old standard deviation 10.0020, modern 2.8845); this is not proof of missing papyrus, absent ink or an anatomical cause.

The nominal catalogue mapping also fails these new controls: reserveA Pearson 0.7430432151/margin 0.0083178694; reserveB 0.0242531989/-0.0422376784. These nominal baselines are later diagnostics, not a way to select an accepted transform. The earlier near-ROI best valid diagnostic margin 0.0918806862 remains below 0.1 and is not superseded by a claim that these broader fits are better.

Training-only local translation diagnostics have block Pearson values 0.8605,0.7032,0.9159,0.4395 and0.9426. The apparent translations differ substantially. A weak or ambiguous block match cannot be treated as an anatomical landmark; these numbers do not prove nonrigid deformation. Identical local diagnostics were reused by SHA for trial2, not rerun.

## Verification and preserved evidence

The independent lab replay verifies frozen artifacts, zero initialization, global fitting objectives, all raw controls/gates and 16 direct 64-midpoint footprints from observed scan bytes. A supplement replays all five local objectives and independently recomputes reserved support separation. Stronger continuous guard separation is at least 3.6276 native voxels, and training/reserve support separation at least 40.2770 modern voxels for these designs. The prior sealed 60-file phase remains byte-identical. Neither verification substitutes absent chunks with fill values.

All computation and analysis runs sequentially with CPUQuota 25%, Nice 19, IOWeight 10, MemoryMax 384MiB, swap 0, GPU inaccessible, five numerical thread limits at 1 and desktop reserve>=3072MiB. The two fit runs peak below 139MiB childRSS and retain over 8,000MiB available desktop memory. Logs, sources, plans, all rejected outputs, independent-review limitations and source hashes are preserved in English. There is no new accepted surface or ink projection.

The compact standard-library replay verifies saved CT arrays and decisions offline; it does not reproduce fitting, scan-byte sampling, anatomy or ink. Full scientific replay uses the lab fixtures, NumPy and SciPy recorded by the preceding coordinate audit. Public source and license references remain in `../paris4-coordinate-audit/SOURCES.json` in the repository export. No universal novelty, prize qualification or recovered text is claimed.

These controls show that the current bounded affine candidates do not transfer reliably to the exterior. A useful next registration investigation needs supported structural correspondences or a deformation hypothesis tested against genuinely reserved spatial regions; increasing bounds, dropping weak blocks or tuning against the inspected ROI is not justified by these results. No application edit, submission or remote publication is performed here.
