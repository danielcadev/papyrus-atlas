"""Prepare English evidence for local review; do not publish or submit anything."""
from pathlib import Path
import json,shutil,subprocess
from ink_guard import require_guard
from ink_io import digest
guard=require_guard();assert guard['memory_max']<=384*1024**2
root=Path(__file__).resolve().parent;case=root/'paris4-independent-validation-v1'
repo=root/'standalone-private-upload-v2/repository'
for name in ('verification-v1.json','verification-supplement-v1.json'):assert json.loads((case/name).read_text())['passed']
assert not subprocess.run(['git','-C',str(repo),'status','--porcelain'],capture_output=True,text=True,check=True).stdout.strip()
old_manifest=json.loads((repo/'MANIFEST.json').read_text())
for row in old_manifest['files']:assert digest(repo/row['path'])==row['sha256']
trials=case/'trials';trials.mkdir(exist_ok=False)
for n in (1,2):shutil.copytree(root/f'paris4-independent-controls-v{n}',trials/f'paris4-independent-controls-v{n}')
logs=case/'execution-records';logs.mkdir(exist_ok=False)
for pattern in ('paris4-independent-blocks-0*','paris4-independent-verify-01.*','paris4-independent-support-01.*'):
    for p in (root/'native').glob(pattern):
        if p.is_file():shutil.copyfile(p,logs/p.name)
sources=case/'lab-source-snapshots';sources.mkdir(exist_ok=False)
for name in ('register_paris4_independent_blocks.py','register_paris4_equal_block_controls.py','verify_paris4_independent_controls.py','complete_paris4_independent_audit.py','prepare_paris4_independent_package.py'):
    shutil.copyfile(root/name,sources/name)
review='''# Independent design and source review

A separate Sol agent reviewed the designs, source and first outputs without scientific computation or file mutation.

The zero residual initializer removes the prior fitted-parameter contamination. Reserved old/native target indices have Z<96, outside the known earlier fit targets and axis anchors. They remain controls within the same two scans, not new scans, anatomical landmarks or statistically independent source measurements. Cached modern intensities were already available.

The reviewer checked the conservative support bound including residual parameter extremes, cache interpolation, 64-point quadrature and raw modern trilinear interpolation. Training supports and each trial's reserved-control supports are strictly separated for the whole allowed parameter box. Source code initially used guardhigh-1 in a projected guard inequality, which only certifies separation from integer guard centers. The preserved source is not silently rewritten. Independent verification checks the stronger continuous guard, including voxel-cell lower extents, and finds at least3.6275898 old/native voxels of strict separating gap. The supplement independently recomputes reserved support boxes and finds at least40.2769965 modern voxels of separation from all five training support boxes. This concerns the specified input data and parameter box, not arbitrary future transforms.

After observing trial1, equal within-block NCC is a defensible exploratory follow-up to pooled-intensity dominance. All five blocks are retained; none is removed for low similarity. Trial1 failures remain prominent. Trial2 evaluates a new target block B while A is already a development diagnostic. B's moving supports may overlap earlier A supports, so B is not statistically independent of A. Both transforms are frozen before their respective reserved-target and original ROI evaluation. The original ROI was previously inspected.

Local translation differences, especially in a weak block with Pearson0.4395, do not establish a deformation field or reliable anatomical point correspondences. Both fitted affines reach an existing linear-parameter bound and fail the unchanged validation gates. No model is admitted.
'''
(case/'INDEPENDENT_REVIEW_EN.md').write_text(review)
report='''# Paris4 spatial controls and cold-start registration

**Registration remains rejected.** Two fresh fits start from the published catalogue affine with exactly zero residual parameters. Neither uses the earlier optimized initializers. No source geometry, UV or recovered face is modified. No ink scores, letters or text are used, and no ink benefit or anatomical registration error bound is demonstrated.

## Fixed design and independence

Five exterior training blocks contain10,240 old/native CT target samples. Each trial uses2,048 newly withheld targets in a separate block with native Z88:96. ReserveA is Y148:164,X116:132; reserveB is Y176:192,X116:132. Plans are written before intensities are loaded. All local diagnostics and the global fit use training only. Global parameters are frozen before querying that trial's reserved targets and the original repaired ROI. Trial2 is an exploratory follow-up after trial1, not a blind preregistered study. The original ROI is previously inspected.

The controls are disjoint from each current fit's training, with conservative support proofs covering all allowed translations, linear residuals, cache interpolation, quadrature and observed modern CT interpolation. They are not manually annotated anatomical control points or statistically independent scans. Previous nominal cache generation already sampled modern intensities, but did not optimize on these reserved old/native target values. The original source guard inequality is qualified by a stronger continuous-support check in the independent verification; see [review](INDEPENDENT_REVIEW_EN.md).

Residual translations are bounded to±2 old voxels and each residual linear entry to±0.01. These are not enlarged after failure. The original admission thresholds remain raw Pearson>=0.6 and margin>=0.1 over the same six±4-old-voxel controls, plus converged fitting without a parameter-boundary solution. This phase strengthens admission by also requiring the new reserved block to pass; it never substitutes the reserve for the original ROI gate.

## Results

| Fit and evaluation | Raw CT Pearson | Margin over strongest shifted control | Decision |
| --- | ---: | ---: | --- |
| Trial1 pooled-intensity affine, fresh reserveA | 0.7149906564 | -0.0200862357 | Reject |
| Trial1, original repaired ROI | 0.8441047337 | 0.0792836814 | Reject |
| Trial2 equal mean of five block NCCs, fresh reserveB | 0.0691782566 | -0.0617534169 | Reject |
| Trial2, original repaired ROI | 0.8345949231 | 0.0694520082 | Reject |
| Trial2, previously inspected reserveA, later diagnostic | 0.6921345062 | -0.0344331939 | Reject |

Both optimizations converge but reach an existing linear-parameter boundary:918 and943 evaluations against a2,048-evaluation/120-second cap. Thus neither is admissible even before considering its failed raw validation gate. The second training objective is the arithmetic mean of within-block correlations, not a pooled Pearson. All five blocks remain included. ReserveB has lower measured intensity variation (old standard deviation10.0020, modern2.8845); this is not proof of missing papyrus, absent ink or an anatomical cause.

The nominal catalogue mapping also fails these new controls: reserveA Pearson0.7430432151/margin0.0083178694; reserveB0.0242531989/-0.0422376784. These nominal baselines are later diagnostics, not a way to select an accepted transform. The earlier near-ROI best valid diagnostic margin0.0918806862 remains below0.1 and is not superseded by a claim that these broader fits are better.

Training-only local translation diagnostics have block Pearson values0.8605,0.7032,0.9159,0.4395 and0.9426. The apparent translations differ substantially. A weak or ambiguous block match cannot be treated as an anatomical landmark; these numbers do not prove nonrigid deformation. Identical local diagnostics were reused by SHA for trial2, not rerun.

## Verification and preserved evidence

The independent lab replay verifies frozen artifacts, zero initialization, global fitting objectives, all raw controls/gates and16 direct64-midpoint footprints from observed scan bytes. A supplement replays all five local objectives and independently recomputes reserved support separation. Stronger continuous guard separation is at least3.6276 native voxels, and training/reserve support separation at least40.2770 modern voxels for these designs. The prior sealed60-file phase remains byte-identical. Neither verification substitutes absent chunks with fill values.

All computation and analysis runs sequentially with CPUQuota25%, Nice19, IOWeight10, MemoryMax384MiB, swap0, GPU inaccessible, five numerical thread limits at1 and desktop reserve>=3072MiB. The two fit runs peak below139MiB childRSS and retain over8,000MiB available desktop memory. Logs, sources, plans, all rejected outputs, independent-review limitations and source hashes are preserved in English. There is no new accepted surface or ink projection.

The compact standard-library replay verifies saved CT arrays and decisions offline; it does not reproduce fitting, scan-byte sampling, anatomy or ink. Full scientific replay uses the lab fixtures, NumPy and SciPy recorded by the preceding coordinate audit. Public source and license references remain in `../paris4-coordinate-audit/SOURCES.json` in the repository export. No universal novelty, prize qualification or recovered text is claimed.

These controls show that the current bounded affine candidates do not transfer reliably to the exterior. A useful next registration investigation needs supported structural correspondences or a deformation hypothesis tested against genuinely reserved spatial regions; increasing bounds, dropping weak blocks or tuning against the inspected ROI is not justified by these results. No application edit, submission or remote publication is performed here.
'''
(case/'REPORT_EN.md').write_text(report)
(root/'PARIS4_INDEPENDENT_CONTROLS_REPORT_EN.md').write_text(report.replace('(INDEPENDENT_REVIEW_EN.md)','(paris4-independent-validation-v1/INDEPENDENT_REVIEW_EN.md)'))
package=repo/'research/paris4-independent-controls';package.mkdir(exist_ok=False)
for name in ('trials','execution-records','lab-source-snapshots'):shutil.copytree(case/name,package/name)
for p in case.iterdir():
    if p.is_file():shutil.copyfile(p,package/p.name)
shutil.copyfile(root/'replay_paris4_independent_saved.py',package/'replay_saved_controls.py')
(package/'README.md').write_text('''# Paris4 spatial control audit

[Report](REPORT_EN.md) and [independent review](INDEPENDENT_REVIEW_EN.md). Two zero-residual-start affine fits fail the unchanged margin>=0.1 and parameter-boundary controls. Newly withheld CT targets are spatially disjoint from current training; they are not independent scans or annotated anatomical landmarks. No ink or letter recovery is demonstrated.

From the repository root, replay saved CT correlations and decisions offline with Python's standard library:

```bash
bash tools/run_guarded.sh paris4-independent-saved-01 120 python3 -I -S "$PWD/research/paris4-independent-controls/replay_saved_controls.py" /tmp/paris4-independent-saved-01
```

Use a unique job/output name. This reproduces saved-array correlations and gates only. Full fitting and direct CT sampling require the recorded lab fixtures, NumPy and SciPy. Original public source attribution and license references remain in the [coordinate audit](../paris4-coordinate-audit/README.md).
''')
with (repo/'README.md').open('a') as stream:stream.write('\n[Spatial control follow-up](research/paris4-independent-controls/README.md): cold-start fits and new reserved CT targets still reject registration; original geometry and the 0.1 minimum remain unchanged.\n')
shutil.copyfile(repo/'MANIFEST.json',case/'repository-manifest-before.json')
# Manifest is refreshed after portable replay receipts are added, before commit.
print(json.dumps(dict(prepared=True,package=str(package),previous_repository_files_verified=len(old_manifest['files']))),flush=True)
