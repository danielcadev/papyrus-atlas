"""Materialize one predeclared real-CT halo fixture; never run a mesher.

Run through run_holefill_guarded.sh. Selection and comparisons are constants,
not options: changing them creates a different experiment requiring a new name.
"""
import hashlib
import json
import os
from pathlib import Path
import shlex
import sys


ROOT = Path(__file__).resolve().parent
BASE = ROOT / 'scrollfiesta-comparison'
DEST = BASE / 'next-zplus32-halo13-v1'
SOURCE = ROOT / 'data/01744_02256_04048_volume.nrrd'
SOURCE_SHA = '3041f5bd3bf5b9d3d68be6a65934c39664d04c2f221ca23561bde0d1376ee110'
BINARIES = {
    'v2': ('cube_mesh.boundary-graft-v2', '417b540d3bb276658b3e3ae8881bdf9de5c85e5677d79132bd471ef8f5cd478a'),
    'v4': ('cube_mesh.holefill-v4', 'a9941000992c0430a071b04c71e6e7fcf178c5610b2fb5bf57f00e98282fdd51'),
}
THREAD_KEYS = ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS',
               'VESUVIUS_THREADS', 'OMP_THREAD_LIMIT')


def sha256(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def require_guard():
    """Fail closed before importing numeric libraries or opening CT."""
    assert all(os.environ.get(key) == '1' for key in THREAD_KEYS), 'Use guarded wrapper with all five thread limits'
    assert os.getpriority(os.PRIO_PROCESS, 0) >= 19, 'Nice=19 required'
    assert not os.access('/dev/dri', os.R_OK) and not os.access('/dev/kfd', os.R_OK), 'GPU must be inaccessible'
    line = next(line for line in Path('/proc/self/cgroup').read_text().splitlines() if line.startswith('0::'))
    group = Path('/sys/fs/cgroup') / line.split('::', 1)[1].lstrip('/')
    quota, period = map(int, (group / 'cpu.max').read_text().split())
    assert quota / period <= .25, 'CPUQuota must be <=25%'
    assert int((group / 'memory.max').read_text()) <= 384 * 1024**2, 'MemoryMax must be <=384MiB'
    assert int((group / 'memory.swap.max').read_text()) == 0, 'MemorySwapMax=0 required'
    io_weight = (group / 'io.weight').read_text().strip()
    assert io_weight == 'default 10', 'IOWeight=10 required'
    from guard import start_guard
    start_guard()
    return {'cgroup': str(group), 'cpu_max': (group / 'cpu.max').read_text().strip(),
            'memory_max': (group / 'memory.max').read_text().strip(),
            'memory_swap_max': '0', 'io_weight': io_weight, 'nice': 19,
            'gpu_inaccessible': True, 'thread_limits': {key: '1' for key in THREAD_KEYS},
            'desktop_reserve_mib': 3072}


RUNNER = '''"""Execute exactly one frozen case, called by run_native_guarded.py."""
import hashlib, json, os, subprocess, sys, time
from pathlib import Path
d = Path(__file__).resolve().parent
record = json.loads((d / 'frozen-input.json').read_text())
preparer = Path(record['research_root']) / 'prepare_next_validation.py'
assert hashlib.sha256(preparer.read_bytes()).hexdigest() == record['preparer_sha256'], 'Frozen preparer changed'
sys.path.insert(0, record['research_root'])
from prepare_next_validation import require_guard, sha256
require_guard()
case = record['cases'][sys.argv[1]]
assert not Path(case['output_directory']).exists(), 'Preserve prior outputs'
assert sha256(Path(case['binary'])) == case['binary_sha256'], 'Frozen binary changed'
assert sha256(d / case['stdin_file']) == case['stdin_sha256'], 'Frozen input changed'
assert sha256(Path(__file__)) == record['runner_sha256'], 'Frozen runner changed'
# An explicit environment prevents inherited experimental switches changing defaults.
env = dict(PATH='/usr/bin:/bin', LANG='C', MLS_EDGE_ADAPT='soft',
           VES_OVERLAP_COVERAGE_GUARD='1', OPENBLAS_NUM_THREADS='1',
           OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', VESUVIUS_THREADS='1',
           OMP_THREAD_LIMIT='1', CUDA_VISIBLE_DEVICES='-1', HIP_VISIBLE_DEVICES='-1',
           ROCR_VISIBLE_DEVICES='', MALLOC_ARENA_MAX='1')
print(json.dumps({'case': sys.argv[1], 'command': case['command'],
                  'stdin': str(d / case['stdin_file']), 'environment': env}), flush=True)
started = time.monotonic()
with (d / (sys.argv[1] + '-started.json')).open('x') as stream:
    json.dump({'state': 'started', 'command': case['command'],
               'stdin_sha256': case['stdin_sha256'], 'binary_sha256': case['binary_sha256']}, stream, indent=2)
with (d / case['stdin_file']).open('rb') as stream:
    result = subprocess.run(case['command'], stdin=stream, env=env, check=False)
with (d / (sys.argv[1] + '-finished.json')).open('x') as stream:
    json.dump({'state': 'process-exited', 'returncode': result.returncode,
               'elapsed_seconds': time.monotonic() - started,
               'pipeline_status_requires_log_review': True}, stream, indent=2)
raise SystemExit(result.returncode if result.returncode >= 0 else 1)
'''


def main():
    assert not DEST.exists(), 'Preserve frozen selection and all prior results'
    guarded = require_guard()
    assert sha256(SOURCE) == SOURCE_SHA, 'CT provenance mismatch'
    for filename, expected in BINARIES.values():
        assert sha256(BASE / 'build' / filename) == expected, 'Frozen binary mismatch'
    import numpy as np
    from inspect_cube import read_nrrd
    volume, _ = read_nrrd(SOURCE)
    assert volume.shape == (256, 256, 256)
    assert volume.dtype in (np.dtype('u1'), np.dtype('<u2'))
    source_dtype = str(volume.dtype)
    divisor = 257 if volume.dtype.itemsize == 2 else 1
    # NRRD native XYZ -> prediction ZYX; exactly one previously undeveloped window.
    window = (volume[112:144, 112:144, 144:176].transpose(2, 1, 0) // divisor).astype('uint8')
    hist = np.bincount(window.ravel(), minlength=256).astype(float)
    probability = hist / hist.sum()
    weights = probability.cumsum()
    means = (probability * np.arange(256)).cumsum()
    score = np.full(256, -np.inf)
    valid = (weights > 0) & (weights < 1)
    assert valid.any(), 'Predeclared window is constant; retain failed selection, do not search'
    score[valid] = (means[-1] * weights[valid] - means[valid])**2 / (weights[valid] * (1 - weights[valid]))
    threshold = int(score.argmax())
    active = (window > threshold).astype('uint8') * 255
    del volume
    DEST.mkdir()
    np.save(DEST / 'raw-active-zyx.npy', window)
    np.save(DEST / 'prediction-active-zyx.npy', active)
    # Source-origin ZYX [1744,2256,4048]. Two nominal cores [128]^3;
    # source-origin cores ZYX [96,64,0] and [96,64,128].
    source_origin = np.array([1744, 2256, 4048])
    roi_low = np.array([144, 112, 112])
    roi_high = roi_low + 32
    inputs = {}
    for side, core_low in [('left', np.array([96, 64, 0])), ('right', np.array([96, 64, 128]))]:
        padded_low = core_low - 13
        padded_high = core_low + 128 + 13
        lo = np.maximum(padded_low, roi_low)
        hi = np.minimum(padded_high, roi_high)
        assert np.all(hi > lo)
        padded = np.zeros((154, 154, 154), dtype='uint8')
        target = tuple(slice(int(a), int(b)) for a, b in zip(lo - padded_low, hi - padded_low))
        source = tuple(slice(int(a), int(b)) for a, b in zip(lo - roi_low, hi - roi_low))
        padded[target] = active[source]
        filename = f'{side}-prediction-zyx.raw'
        padded.tofile(DEST / filename)
        inputs[side] = {'stdin_file': filename, 'stdin_sha256': sha256(DEST / filename),
                        'bytes': int(padded.size), 'core_low_source_zyx': core_low.tolist(),
                        'origin_world_zyx': (source_origin + core_low).tolist(),
                        'padded_low_source_zyx': padded_low.tolist(),
                        'padded_shape_zyx': [154, 154, 154],
                        'active_context_source_zyx': [lo.tolist(), hi.tolist()],
                        'foreground_voxels': int(np.count_nonzero(padded))}
    # Check exact global overlap, without evaluating any geometric outcome.
    left = np.fromfile(DEST / inputs['left']['stdin_file'], dtype='uint8').reshape(154, 154, 154)
    right = np.fromfile(DEST / inputs['right']['stdin_file'], dtype='uint8').reshape(154, 154, 154)
    assert np.array_equal(left[:, :, 128:154], right[:, :, :26]), 'Global halo overlap mismatch'
    (DEST / 'run_case.py').write_text(RUNNER)
    cases = {}
    commands = []
    for version, (filename, digest) in BINARIES.items():
        for side, item in inputs.items():
            name = f'{version}-{side}'
            output = DEST / f'{name}-obj'
            binary = BASE / 'build' / filename
            command = [str(binary), '--stdin-raw', '154', *map(str, item['origin_world_zyx']),
                       '--halo', '13', '--trim-inset', '1', '--dump-obj', str(output), '--no-simplify']
            launch = ['bash', str(ROOT / 'run_holefill_guarded.sh'), f'next-z32-h13-{name}-01',
                      '900', sys.executable, str(DEST / 'run_case.py'), name]
            cases[name] = dict(item, binary=str(binary), binary_sha256=digest, command=command,
                               output_directory=str(output), guarded_launch=launch)
            commands.append(shlex.join(launch))
    record = {
        'experiment': DEST.name, 'research_root': str(ROOT), 'fixture_status': 'prepared-not-run',
        'selection': 'Single +32Z window, fixed before outcomes; no alternative search or label access',
        'source_volume': str(SOURCE), 'source_sha256': SOURCE_SHA,
        'source_shape_xyz': [256, 256, 256], 'source_dtype': source_dtype,
        'source_dataset': 'PHercParis4 harmonized manual-instance CT collection, 2024-10',
        'source_axes': 'NRRD XYZ; raw stdin C-order ZYX; all intervals half-open',
        'source_origin_world_zyx': source_origin.tolist(),
        'active_roi_source_xyz': [[112, 112, 144], [144, 144, 176]],
        'active_roi_source_zyx': [roi_low.tolist(), roi_high.tolist()],
        'threshold_exclusive': threshold, 'otsu_tie_break': 'first maximum',
        'intensity_divisor': divisor, 'foreground_voxels': int(np.count_nonzero(active)),
        'manual_labels_opened': False, 'raw_padding': 'Prediction is zero outside fixed active ROI; no CT intensities synthesized',
        'overlap_input_equal': True, 'inputs': inputs, 'cases': cases,
        'runner_sha256': sha256(DEST / 'run_case.py'), 'preparer_sha256': sha256(Path(__file__)),
        'guard_at_preparation': guarded,
        'parameters': {'halo': 13, 'owned_core': 128, 'trim_inset': 1,
                       'mls_mode': 'soft', 'overlap_coverage_guard': 1, 'no_simplify': True},
        'seam_world_x': 4176, 'expected_trim_planes_world_x': [4175, 4177],
        'expected_gap_voxels': 2,
        'budget': {'preparation_timeout_seconds': 120, 'each_meshing_timeout_seconds': 900,
                   'maximum_meshing_seconds': 3600, 'memory_max_mib': 384,
                   'cpu_quota_percent': 25, 'sequential_only': True,
                   'preparation_estimate_peak_mib_below': 150, 'meshing_peak_not_yet_measured': True},
        'limitations': ['New window, same CT cube and same scroll already used for development; no independent cube/scroll holdout',
                        'Otsu baseline with artificial zero prediction outside32^3; no trained predictor',
                        'Halo13 omits3 active context slices at each remote ROI edge; both versions get identical input',
                        'Adjacent owned cores are shifted local partitions, not an official dataset tiling',
                        'Ownership trim is tested; the expected gap2 is not a weld or seamless-surface certificate'],
    }
    (DEST / 'frozen-input.json').write_text(json.dumps(record, indent=2) + '\n')
    (DEST / 'commands.sh').write_text('#!/usr/bin/env bash\nset -euo pipefail\n# Run serially, after reviewing PROTOCOL.md. Never append &.\n' + '\n'.join(commands) + '\n')
    (DEST / 'PROTOCOL.md').write_text(PROTOCOL)
    print(json.dumps({'prepared': str(DEST), 'threshold': threshold,
                      'commands': str(DEST / 'commands.sh'), 'not_executed': list(cases)}), flush=True)


PROTOCOL = '''# Predeclared +32Z halo/ownership comparison

Purpose: exercise real halo extraction and final ownership clipping after the
geometric hole-fill duplicate correction, with frozen v2 versus v4. The new
window is disjoint in its interior from central/+32X/+32Y development windows,
but shares their CT cube and scroll. This is not an independent holdout cube.

Read frozen-input.json first. commands.sh runs v2-left, v2-right, v4-left,
v4-right serially, through systemd + run_native_guarded.py + guard.py. Each
case has a900s deadline,384MiB cap,25% CPU quota, five one-thread limits,
Nice19, IOWeight10, swap0, GPU inaccessible and desktop reserve3072MiB.
Preparation timeout120s; meshing total<=3600s; geometry evaluation is a separate
guarded job, preferably<=600s. A failure is evidence: retain it, do not select
another window, modify parameters or overwrite paths. All four inputs/binaries
are hashed before geometry runs; the runner verifies them again.

stdin is explicitly opened binary and passed to subprocess.run; it is not a
shell redirection through systemd. No TIFF-neighbor lookup is involved. Native
coordinates are XYZ; VMESH dumps are globalZYX. Left core worldZYX origin is
[1840,2320,4048], right is [1840,2320,4176]. Shared ownership plane worldX4176;
explicit trim-inset1 clips left at4175 and right at4177. The expected gap2 is
intentional. Do not call it a new crack or a validated weld.

After each successful mesher run, require Status:OK and record every final
Guard counter, trim counts, timings, max cgroup memory and return status. Use
step12_final_all.vmesh (halo mode), not step11_kibble as the final result.
Failure or an empty mesh is a reported outcome, never a reason to retune.

Evaluate both versions with the same guarded native auditor, gap_max0 and all
charts included. Preserve the four auditor predicate controls. Report per-core
and combined conflicts/overlaps/stabs/folds, exact geometric duplicate groups,
face counts and area. To combine a version's two final VMESHs, retain stored
globalZYX floats and concatenate faces with index offsets; do not translate the
right mesh a second time. The existing auditor's common origin can be the left
origin[1840,2320,4048]; its local XYZ conversion must apply that SAME origin to
both meshes. Keep the original meshes and label the union as an audit artifact.

Compare v2/v4 per-core step7_cc_bpa sources bytewise, then directed geometric
face multisets step7->step8 to record source preservation; do not demand source
triangle preservation after final trim, which legitimately clips faces. Audit
all pieces before trim as well as step12 to avoid hiding internal conflicts by
clipping. Report every difference even when the patch is neutral. Desired
nonregression: no source-face loss at hole-fill and no additional conflicts or
exact duplicates versus v2; do not assume either baseline starts at zero.

For seam geometry, report distance of left/right boundary vertices to their
expected trim planes, symmetric point-to-triangle distance across the boundary
bands, and the unmatched boundary fraction. Use the full boundary band within
4voxels of each expected plane; report sample count and empty bands explicitly.
Distances include the intended2voxel gap and geometry/context differences, so
they are descriptive metrics, not a weld score or anatomical correspondence.
No manual labels are used for preparation. Any later label coverage is post-hoc,
counts all IDs and cannot establish same-sheet identity. Do not claim full-roll
validation, new-scroll transfer, or general superiority from this fixture.
'''


if __name__ == '__main__':
    main()
