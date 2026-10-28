"""Snapshot v5 sources and hash evidence without replacing prior results."""
import json
from pathlib import Path
import shutil
from prepare_next_validation import require_guard, sha256

guard = require_guard()
root = Path(__file__).resolve().parent
base = root / 'scrollfiesta-comparison'
dest = base / 'hole-recovery-v5'
output = dest / 'evidence-manifest-v1.json'
assert not output.exists()
snapshot = dest / 'source-v5'
snapshot.mkdir(exist_ok=False)
for name in ('hole_fill.c', 'hole_recovery_search.inc'):
    shutil.copy2(base / 'source/src/holefill' / name, snapshot / name)
paths = set(p for p in dest.rglob('*') if p.is_file())
paths.update(base / 'build' / name for name in ('cube_mesh.holefill-v5', 'replay_holefill.v5'))
paths.update(root / name for name in (
    'exact_mesh_certificate.py', 'exact_patch_intersections.py', 'certify_patch_coverage.py',
    'verify_patch_coverage_witnesses.py', 'test_verify_patch_coverage_witnesses.py',
    'test_exact_mesh_certificate.py',
    'test_exact_patch_intersections.py', 'test_certify_patch_coverage.py',
    'evaluate_full_hole_recovery_v5.py', 'certify_replay_v5.py',
    'freeze_hole_recovery_v5.py', 'hole_recovery_candidate.c',
    'hole_recovery_search.inc', 'hole_recovery_production_proposal.patch',
    'HOLE_RECOVERY_PRODUCTION.md', 'HOLE_TOPOLOGY_REVIEW.md',
    'check_hole_recovery_regressions_v5.py', 'check_hole_recovery_halo_v5.py',
    'run_saved_core_weld.py', 'saved_core_weld.c',
    'CORE_CONTINUITY_NEXT_DECISION.md', 'PARIS4_CONTEXT_REVIEW.md',
    'PARIS4_BRANCH_ACCEPTANCE.md', 'diagnose_paris4_local_branches.py',
    'PARIS4_LOCAL_BRANCH_RESULT.md',
    'PARIS4_ORTHOGONAL_REVIEW.md', 'CONTINUOUS_COVERAGE_REVIEW.md',
    'CONTRIBUTION_DRAFT.md', 'VALIDATION_SCOPE.md'))
paths.add(root.parent / 'CONTEXT.md')
paths.update(root / 'data' / name for name in (
    '01744_02256_04048_volume.nrrd', '01744_02256_04048_mask.nrrd', 'manifest.json'))
for folder in base.glob('core-weld-*'):
    if folder.is_dir():
        paths.update(p for p in folder.rglob('*') if p.is_file())
halo = base / 'next-zplus32-halo13-v1'
paths.add(halo / 'frozen-input.json')
for name in ('evaluation-v2', 'continuity-diagnostic-v1'):
    paths.update(p for p in (halo / name).rglob('*') if p.is_file())
for pattern in ('hf-recovery-*', 'hf-full-y32-v5-01.*', 'core-weld-*', 'paris4-*'):
    for path in (root / 'native').glob(pattern):
        if path.is_dir():
            paths.update(p for p in path.rglob('*') if p.is_file())
        elif path.is_file():
            paths.add(path)
assert all(p.is_file() for p in paths), 'Required evidence missing'
manifest = dict(schema='hole-recovery-v5-evidence-v1', guard=guard,
                purpose='Immutable input/source/output and local evidence digests; not a new scientific validation',
                files=[dict(path=str(p.relative_to(root.parent)), bytes=p.stat().st_size,
                            sha256=sha256(p)) for p in sorted(paths)])
with output.open('x') as stream:
    json.dump(manifest, stream, indent=2)
    stream.write('\n')
print(json.dumps(dict(output=str(output), files=len(manifest['files']))))
