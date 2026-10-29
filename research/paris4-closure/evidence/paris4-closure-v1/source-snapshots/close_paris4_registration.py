"""Archive the unresolved Paris4 registration work at the user's request."""
from pathlib import Path
import json,shutil
from ink_guard import require_guard
from ink_io import digest
guard=require_guard();assert guard['memory_max']<=384*1024**2
root=Path(__file__).resolve().parent;out=root/'paris4-closure-v1';out.mkdir(exist_ok=False)
cases=['paris4-structural-matches-v1','paris4-structural-direct-v2','paris4-structural-face-selection-v1',
       'paris4-structural-face-direct-v3','paris4-structural-context-v1','paris4-structural-audit-v1']
audit=json.loads((root/'paris4-structural-audit-v1/verification-v1.json').read_text());assert audit['passed']
hull=json.loads((root/'paris4-structural-audit-v1/face-hull-design-review.json').read_text());assert hull['passed'] and not hull['full_selected_hull_can_contain_required_ROI']
for name in cases:
    case=root/name
    record=case/'result.json'
    if record.exists():
        r=json.loads(record.read_text())
        for relative,sha in r.get('artifacts',{}).items():assert digest(case/relative)==sha
shutil.copyfile(root.parent/'CONTEXT.md',out/'CONTEXT-before-closure.md')
sources=out/'source-snapshots';sources.mkdir()
for name in ('close_paris4_registration.py','match_paris4_structural_points.py','match_paris4_direct_structural_points.py',
             'select_paris4_face_structures.py','match_paris4_face_structural_points.py',
             'render_paris4_structural_context.py','verify_paris4_structural_matches.py','check_paris4_face_hull_preflight.py'):
    shutil.copyfile(root/name,sources/name)
report='''# Paris4 registration closure and PHerc0813 handoff

The user requested closing the active Paris4 investigation and resuming PHerc0813. Paris4 is closed for prioritization, with registration UNVALIDATED. This is not a successful registration, proof of blank papyrus, proof that elastic deformation is necessary, or a universal impossibility result. No failed transform is admitted and no source surface or UV is changed.

## What remains established

The dataset-specific old NRRD ZYX convention passes its same-scan CT anchor audit (reserved-plane Pearson approximately0.99905). This does not validate cross-scan registration. The best earlier local cross-scan margin remains0.0918806862, below the unchanged0.1 minimum, with Pearson>=0.6 still required. Broader cold-start affine trials fail new spatial controls and reach their linear parameter bounds. Original geometry algorithm results are separate from these registration failures.

Corrected nominal published-ink queries on graft additions yield raw values1–13 and on hole additions1–2. These are third-party predictions under a nominal mapping; they do not establish physical absence of ink or recovered letters. No real-ink benefit is demonstrated.

## Latest structural trials

The old-only corner selector found16 candidates. A cache-based pilot marked4 provisional matches after its local checks. An exact direct64-midpoint observed-CT rematch of all16 retained none under the stricter direct/reciprocal criteria. A distinct old-only face selector found12 candidates; its direct matching also retained none. Minimum local/registration margins were not lowered. No translation model was constructed; the freshC region was not evaluated for admission. Global old-crop filters did read C/ROI input bytes, but finite supports of selected outputs are verified disjoint from them.

Two implementation/design limitations are explicitly preserved. First, the cache pilot's correlation routine centered float64 witness arrays in place; original candidate-direct-modern files are centered data despite their name. The independent audit writes five separate raw witnesses and reproduces the centered historical files without overwriting them. NCC decisions are unaffected. Second, the12 face-selected centers cannot enclose the full required ROI: every center has z-y+x<=133 while ROI corner[143,144,143] has value142. This exact separating-plane witness proves that the trial could not pass its own hull prerequisite even if all matches succeeded. It is a selection-design error, not a physical impossibility. Any future selector must check full-selected-hull feasibility before expensive matching. The face trial never reached its continuous reverse branch, so no empirical continuous-reciprocity success is claimed.

The independent audit replays28 direct patch forward/control decisions, competing grid peaks, selected-filter exclusions, raw witnesses and scalar-versus-vectorized quadrature. The maximum footprint discrepancy is approximately7.1e-15. Grid competitors are finite sampling, not proof of continuous global uniqueness. The previous64-file sealed phase remains unchanged. The fixed-window orthogonal CT figure shows differing image sharpness; PSF/energy/masking effects remain hypotheses, not established causes.

## Preservation and next objective

All trial outputs, sources, failure reasons, acquisition references, figure and checks are retained under the closure inventory. The original0.1 margin and all resource protections remain unchanged: CPUQuota25%, Nice19, IOWeight10, MemoryMax384MiB, no swap, GPU inaccessible, one numerical thread and desktop reserve>=3072MiB. No application is closed and nothing is submitted or published by this closure.

The active research priority becomes PHerc0813. Resume from ph​​erc0813-reference-front-v1/accepted-result-v2.json (48,643 faces), with exact same-center width0.7592460388423183mm and exact chart area0.9197373956087804mm2. Reader requirements remain1.2288mm and1.50994944mm2. The saved source retains its geometry and revised-map UV contract; no ink inference or letters are verified. Source hashes, complete validations and sealed prior evidence must be checked before proposing a materially different growth direction. Do not repeat exhausted corner ears/fans/chains or an identical failed global UV solve.
'''.replace('ph​​erc','pherc')
(out/'REPORT_EN.md').write_text(report)
(root/'PARIS4_CLOSURE_REPORT_EN.md').write_text(report)
entries={}
for name in cases:
    for p in sorted((root/name).rglob('*')):
        if p.is_file():entries[p.relative_to(root).as_posix()]=dict(bytes=p.stat().st_size,sha256=digest(p))
for p in sorted(out.rglob('*')):
    if p.is_file():entries[p.relative_to(root).as_posix()]=dict(bytes=p.stat().st_size,sha256=digest(p))
manifest=out/'evidence-manifest-v1.json';manifest.write_text(json.dumps(dict(schema='paris4-closure-root-relative-v1',
    path_base='lab research directory',files=entries,file_count=len(entries)),indent=2)+'\n')
for relative,row in entries.items():assert digest(root/relative)==row['sha256']
result=dict(guard=guard,closed_at_user_request=True,registration_validated=False,ink_absence_proved=False,
    geometric_algorithms_refuted=False,letters_verified=0,next_priority='PHerc0813',file_count=len(entries),manifest_sha256=digest(manifest),
    source_geometry_modified=False,pushed_or_submitted=False)
(out/'closure-verification.json').write_text(json.dumps(result,indent=2)+'\n')
context=root.parent/'CONTEXT.md';text=context.read_text()
section='''### Active priority: PHerc0813; Paris4 registration closed at user request

The user explicitly requested closing Paris4 and continuing PHerc0813. Closure: research/PARIS4_CLOSURE_REPORT_EN.md, inventory research/paris4-closure-v1/evidence-manifest-v1.json. Paris4 registration remains unvalidated; weak published predictions are not proof of blank papyrus or absence of ink. No claim that nonrigid deformation is necessary. The16 direct corner and12 direct face patch matches yield0 reliable points; no model is built and freshC is not evaluated for admission. Five mean-centered historical witnesses have separate corrected raw copies in the structural audit. Face-selector hull defect is verified by exact separating plane: all12 z-y+x<=133, required corner=142. Future selectors need hull feasibility preflight; do not repeat this set or count it as physical impossibility. All latest structural evidence is inventoried unchanged. No publication, submission or geometry change.

Resume PHerc0813 from accepted-result-v2.json in research/pherc0813-reference-front-v1 and its complete retained world/map, not bulk or failed trial maps.48643 faces; exact centered width.7592460388423183mm, exact chart area.9197373956087804mm2, reader target1.2288mm/1.50994944mm2, no ink inference or verified letters. Verify source hashes and prior seals, then choose materially different reference/front or justified chart method. Preserve all source geometry, old maps, exact contact/metric/reference limits and384MiB/25%CPU/no swap/noGPU/one-thread/3072MiB reserve. The existing same-reference corner ears/fans/chains and unchanged whole-chart failure must not be repeated.

'''
context.write_text(text.replace('## Current objective\n\n','## Current objective\n\n'+section,1))
print(json.dumps(result),flush=True)
