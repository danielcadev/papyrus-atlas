"""Prepare the authorized local research commit without changing frozen trials."""
from pathlib import Path
import json,shutil,subprocess
from ink_guard import require_guard
from ink_io import digest
guard=require_guard();assert guard['memory_max']<=384*1024**2
root=Path(__file__).resolve().parent;case=root/'paris4-exterior-registration-v2'
repo=root/'standalone-private-upload-v2/repository'
assert json.loads((case/'verification-v1.json').read_text())['passed']
assert not subprocess.run(['git','-C',str(repo),'status','--porcelain'],capture_output=True,text=True,check=True).stdout.strip()
old_manifest=json.loads((repo/'MANIFEST.json').read_text())
for row in old_manifest['files']:assert digest(repo/row['path'])==row['sha256']
trial_names=('paris4-exterior-collar-v1','paris4-exterior-gradient-v1','paris4-exterior-gradient-support-v2')
trials=case/'trials';trials.mkdir(exist_ok=False)
for name in trial_names:shutil.copytree(root/name,trials/name)
failed=case/'failed-verification-v1';shutil.copytree(root/'paris4-exterior-registration-v1',failed)
logs=case/'execution-records';logs.mkdir(exist_ok=False)
for pattern in ('paris4-exterior-collar-01.*','paris4-exterior-gradient-01.*','paris4-exterior-gradient-support-02.*','paris4-exterior-verify-0*'):
    for path in (root/'native').glob(pattern):
        if path.is_file():shutil.copyfile(path,logs/path.name)
sources=case/'lab-source-snapshots';sources.mkdir(exist_ok=False)
for name in ('fit_paris4_exterior_collar.py','fit_paris4_exterior_gradient.py','fit_paris4_exterior_gradient_support.py',
             'verify_paris4_exterior_registration.py','prepare_paris4_exterior_commit.py'):
    shutil.copyfile(root/name,sources/name)
index=dict(valid_but_rejected_trials=[trial_names[0],trial_names[2]],
    invalid_trial=dict(name=trial_names[1],reason='Central-difference endpoints enter the four-voxel exclusion band. Preserved but excluded from accepted-protocol comparisons. The first independent verifier correctly failed.'),
    previous_phase='paris4-registration-anchors-v1',previous_manifest_sha256=digest(root/'paris4-registration-anchors-v1/evidence-manifest-v1.json'),
    source_nrrd_sha256='3041f5bd3bf5b9d3d68be6a65934c39664d04c2f221ca23561bde0d1376ee110',
    source_urls_and_license='../paris4-coordinate-audit/SOURCES.json',
    registration_accepted=False,ink_used=False,letters_verified=0,geometry_or_uv_modified=False)
(case/'INDEX.json').write_text(json.dumps(index,indent=2)+'\n')
report='''# Paris4 exterior CT registration follow-up

Registration remains rejected. The minimum raw-CT Pearson of 0.6 and margin of 0.1 over the same six four-voxel shift controls were preserved. No fitted transform was admitted, no geometry or UV was changed, and no ink or letter recovery is demonstrated.

## Experiments

The verified native-NRRD-to-old-volume ZYX convention and catalogue affine were retained. Both valid trials reuse the SHA-pinned 88³ matched-footprint grid and fit only CT outside the repaired 32³ ROI plus its four-voxel exclusion band. Residual translation is bounded to ±4 old voxels and each linear residual entry to ±0.01. Each fit is capped at 2,048 evaluations and 120 seconds. The parameters are frozen before raw ROI validation. Validation samples modern CT directly with the same 64-midpoint voxel footprint and six original shift controls.

| Trial | Fit samples / reserved exterior samples | Raw validation Pearson | Best shifted control | Margin | Decision |
| --- | ---: | ---: | ---: | ---: | --- |
| Closer exterior collar, intensity objective | 8,195 / 8,194 | 0.8578014078 | 0.7664491471 | 0.0913522607 | Reject |
| Exterior central differences, support corrected | 7,564 / 7,564 | 0.8580502838 | 0.7661695976 | 0.0918806862 | Reject |

Both valid fits converge inside their parameter bounds: 455 and 546 evaluations. The collar's reserved intensity correlation is 0.9060905 versus 0.9056019 at its initial transform. The corrected gradient fit's reserved gradient correlation is 0.6720256 versus 0.6702205 initially. These are different objectives and must not be compared as if both measured raw intensity similarity. Reserved points alternate spatially with training points; they are correlated neighboring samples, not an independent scan. The repaired ROI has been inspected in previous work and is not an untouched holdout. This follow-up is exploratory, with fixed per-fit plans, not a preregistered blind evaluation.

The prior valid corner-block affine remains the best recorded valid margin, 0.0916497, until the corrected gradient trial improves that diagnostic slightly to 0.0918807. This small change does not meet 0.1 and does not demonstrate an anatomical improvement or a measured registration error bound. The limiting control is still the +4 native-Z shift. Old-CT self-correlation has a diagnostic margin of 0.1478457 against the same shifts; this neither establishes attainability across scans nor replaces the admission gate.

## Preserved invalid attempt

`paris4-exterior-gradient-v1` is INVALID for the intended exclusion protocol. Although its centers lie outside the exclusion band, some central-difference endpoints enter that band. The first independent verifier detects this and exits with an assertion failure. Its source, plan, fit, raw output and failure logs are preserved. Its margin of 0.0920043 is not counted as a valid result. A new trial expands center exclusion by one voxel and passes the complete endpoint-support check. No old outputs were edited or overwritten.

## Verification and limits

The independent lab verifier checks input hashes, training/reserved disjointness and derivative support, both fitting objectives, all raw validation correlations and unchanged gates. It recomputes eight direct 64-midpoint CT footprints from observed scan bytes across the two valid trials. All 120 files of the preceding sealed coordinate-audit phase remain byte-identical. No missing CT is replaced by fill values. Runtime guards retain CPUQuota=25%, Nice=19, IOWeight=10, MemoryMax=384MiB, no swap, GPU inaccessible, all five numerical thread limits at one and at least 3,072MiB available desktop reserve. Fit process peaks are below 133MiB child RSS; each run has its resource receipt.

`replay_saved_controls.py` offers a small offline standard-library replay of the saved raw CT correlations and gate decisions. It does not reproduce optimization, source sampling, anatomical correspondence or ink. The lab source snapshots need the existing lab data layout, NumPy and SciPy. Source object references, hashes and license information remain in the preceding coordinate audit. The published 3D ink field is not used in any fit, and no new score projection is admitted.

A useful next investigation needs independent exterior CT landmarks or a physically supported deformation model with reserved spatial blocks. Repeating affine optimizations or selecting parameters to cross the inspected ROI threshold would not supply that evidence. None of these rejected transforms is suitable for claiming recovered text.

Only a local evidence commit is authorized here. No push, application edit or submission is performed.
'''
(case/'REPORT_EN.md').write_text(report)
(root/'PARIS4_EXTERIOR_REGISTRATION_REPORT_EN.md').write_text(report)
package=repo/'research/paris4-exterior-registration';package.mkdir(exist_ok=False)
for name in ('trials','failed-verification-v1','execution-records','lab-source-snapshots'):shutil.copytree(case/name,package/name)
for name in ('old-native-validation-zyx.npy','verification-v1.json','INDEX.json','REPORT_EN.md'):shutil.copyfile(case/name,package/name)
shutil.copyfile(root/'replay_paris4_exterior_controls.py',package/'replay_saved_controls.py')
(package/'README.md').write_text('''# Paris4 exterior registration follow-up

[Report and limitations](REPORT_EN.md). Two valid CT-only fits remain below the unchanged 0.1 margin. One derivative-support protocol error and its verifier failure are preserved and excluded from valid results. No geometry, ink or letter recovery claim changes.

From the repository root, replay the saved raw-CT correlations offline with Python's standard library:

```bash
bash tools/run_guarded.sh paris4-exterior-controls-01 120 python3 -I -S "$PWD/research/paris4-exterior-registration/replay_saved_controls.py" /tmp/paris4-exterior-controls-01
```

Use unique job and output names. This checks the saved arrays and gates only. Full lab fitting and direct scan-byte verification require the documented lab fixtures and dependencies; these are not a standalone registration reproduction package. Source data and attribution are recorded in [the coordinate audit](../paris4-coordinate-audit/README.md).
''')
with (repo/'README.md').open('a') as stream:stream.write('\nLatest CT-only follow-up: [exterior registration evidence](research/paris4-exterior-registration/README.md). Registration remains rejected at the unchanged 0.1 margin; no verified ink or letters.\n')
shutil.copyfile(repo/'MANIFEST.json',case/'repository-manifest-before.json')
entries=[]
for p in sorted(repo.rglob('*')):
    relative=p.relative_to(repo)
    if not p.is_file() or '.git' in relative.parts or '__pycache__' in relative.parts or relative.as_posix().startswith('tools/native/') or relative.as_posix()=='MANIFEST.json':continue
    entries.append(dict(path=relative.as_posix(),bytes=p.stat().st_size,sha256=digest(p)))
(repo/'MANIFEST.json').write_text(json.dumps(dict(schema='papyrus-atlas-paris4-exterior-followup-v1',
    sealed_software_archive_sha256=old_manifest['sealed_software_archive_sha256'],files=entries),indent=2)+'\n')
print(json.dumps(dict(prepared=True,files=len(entries),package=str(package))),flush=True)
