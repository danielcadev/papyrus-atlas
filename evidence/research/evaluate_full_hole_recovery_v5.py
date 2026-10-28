"""Evaluate a completed +32Y v5 pipeline, reusing identical saved geometry.

Run only under run_holefill_guarded.sh. --log identifies the completed pipeline
log; output is exclusive. A nonzero exit is a failed/incomplete evaluation.
No generation, editing of meshes, or overwrite of historical evidence occurs.
"""
from pathlib import Path
from collections import Counter
import argparse
import ast
import hashlib
import itertools
import json
import re
import struct
import subprocess
import sys

import numpy as np
from guard import start_guard
from independent_split_common import areas, point_to_triangles
from inspect_cube import read_nrrd
from exact_mesh_certificate import inspect_mesh, cyclic_key

P = Path(__file__).resolve().parent
B = P / 'scrollfiesta-comparison'
D = B / 'hole-recovery-v5'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def write_json(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def saved_helpers():
    # The existing evaluator has top-level writes and cannot safely be imported.
    # Reuse only its three function definitions, never its main program.
    path = P / 'evaluate_saved_hole_candidate.py'
    tree = ast.parse(path.read_text(), filename=str(path))
    names = {'read', 'stage', 'sample'}
    functions = [node for node in tree.body
                 if isinstance(node, ast.FunctionDef) and node.name in names]
    require({node.name for node in functions} == names and len(functions) == 3,
            'Saved evaluator helper definitions changed; inspect before reuse')
    module = ast.Module(body=functions, type_ignores=[])
    namespace = {'np': np, 'struct': struct, 'areas': areas}
    exec(compile(module, str(path), 'exec'), namespace)
    return namespace['read'], namespace['stage'], namespace['sample'], digest(path)


def indexed_counter(faces):
    return Counter(cyclic_key(tuple(map(int, face))) for face in faces)


def stats(values):
    require(len(values) > 0, 'Cannot report empty distance samples')
    return dict(count=len(values), median=float(np.median(values)),
                p95=float(np.percentile(values, 95)), max=float(values.max()),
                farther_than_quarter=int((values > .25).sum()),
                farther_than1=int((values > 1).sum()))


def new_face_indices(faces, source_counter):
    remaining = source_counter.copy()
    added = []
    for i, face in enumerate(faces):
        key = cyclic_key(tuple(map(int, face)))
        if remaining[key]:
            remaining[key] -= 1
        else:
            added.append(i)
    require(not +remaining, 'Missing source indices when identifying added faces')
    return added


def measure(v, f, v4v, v4f, oldpath, read, sample):
    """Same samples, reference ROI and support rule as saved evaluator."""
    oldroot = B / 'fresh-yplus32-v2'
    ov, of = read(oldpath)
    local = (v - [1808, 2320, 4112])[:, ::-1]
    tri = local[f]
    oldtri = ((ov - [1808, 2320, 4112])[:, ::-1])[of]
    v4tri = ((v4v - [1808, 2320, 4112])[:, ::-1])[v4f]
    key = lambda t: tuple(sorted(map(tuple, t)))
    beforekeys = {key(t) for t in v4tri}
    removed = np.array([t for t in oldtri if key(t) not in beforekeys])
    samples, weights = sample(tri)
    require(len(samples) <= 1000000, 'Sample budget exceeded')
    labels, _ = read_nrrd(P / 'data/01744_02256_04048_mask.nrrd')
    frozen = json.loads((oldroot / 'frozen-input.json').read_text())
    lo, hi = np.array(frozen['active_roi_source_xyz'])
    prediction = np.load(oldroot / 'prediction.npy') > 0
    rounded = np.rint(samples).astype(int)
    covered = set()
    supported = np.zeros(len(samples), dtype=bool)
    for delta in itertools.product((-1, 0, 1), repeat=3):
        q = rounded + delta
        close = np.linalg.norm(q - samples, axis=1) <= 1
        good = close & ((q >= 0) & (q < 128)).all(1)
        ix = np.flatnonzero(good)
        supported[ix] |= prediction[tuple(q[ix, ::-1].T)]
        ref = q + 64
        good = close & ((ref >= lo) & (ref < hi)).all(1)
        ref = ref[good]
        ref = ref[labels[tuple(ref.T)] > 0]
        covered.update(np.ravel_multi_index(ref.T, labels.shape))
    coverage_ids = Counter(map(int, labels[np.unravel_index(
        np.array(sorted(covered), dtype=int), labels.shape)]))
    probes = json.loads((oldroot / 'frozen-source-probes.json').read_text())
    boundary = np.array([float(point_to_triangles(tri, q).min())
                         for q in probes['boundary_parent_xyz']])
    oldfill_samples, _ = sample(removed)
    oldfill_distance = np.array([float(point_to_triangles(tri, q).min())
                                 for q in oldfill_samples])
    added = new_face_indices(f, indexed_counter(v4f))
    new_samples, _ = sample(local[f[added]])
    new_to_old = np.array([float(point_to_triangles(oldtri, q).min())
                           for q in new_samples])
    return dict(vertices=len(v), faces=len(f), area_voxel2=float(areas(tri).sum()),
                reference_coverage_radius1=len(covered),
                reference_coverage_by_id=dict(coverage_ids),
                ct_otsu_supported_area_radius1=float(weights[supported].sum()),
                samples=len(samples), source_boundary=stats(boundary),
                old_rejected_fill_sample_distance_to_candidate=stats(oldfill_distance),
                new_fill_sample_distance_to_v2_surface=stats(new_to_old))


def evaluate(args):
    args.output.mkdir(parents=True, exist_ok=False)
    report = {'schema': 'full-hole-recovery-v5-evaluation-v1', 'passed': False,
              'obj_root': str(args.obj_root.resolve()), 'log': str(args.log.resolve()),
              'checks': {}, 'stages': {}}
    try:
        read, stage, sample, helpers_sha = saved_helpers()
        report['saved_evaluator_sha256'] = helpers_sha
        log = args.log.read_text()
        report['log_sha256'] = digest(args.log)
        require('Status: OK' in log, 'Pipeline did not report Status: OK')
        guard_lines = [line for line in log.splitlines() if 'Guard:' in line]
        clean_guard = 'Guard: 0 NM-edge(s) (-0 faces), 0 pinch split(s), 0 reorient flip(s)'
        require(guard_lines and all(clean_guard in line for line in guard_lines),
                'Pipeline guard absent or changed geometry')
        require('boundary recovery: 27 faces' in log, 'Expected 27 graft faces not reported')
        require(re.search(r'\[hole_recovery\].*n=19 result=candidate\b', log),
                'Bounded recovery of the 19-cycle not reported')
        report['checks']['pipeline_ok_guard_zero_and_recovery_reported'] = True

        v4root = B / 'holefill-repair-v4/y32-obj'
        source = stage(v4root, 'step7_cc_bpa')
        current_source = stage(args.obj_root, 'step7_cc_bpa')
        require(current_source.read_bytes() == source.read_bytes(),
                'Full pipeline step7 differs from frozen v4')
        report['checks']['step7_byte_identical_to_v4'] = True
        report['step7'] = {'path': str(current_source), 'sha256': digest(current_source)}
        source_facts = inspect_mesh(source)
        require(source_facts.report['faces'] == 5139, 'Unexpected source count')
        sv, sf = read(source)
        sc = indexed_counter(sf)
        v4path = stage(v4root, 'step11_kibble')
        v4facts = inspect_mesh(v4path)
        v4v, v4f = read(v4path)
        v4c = indexed_counter(v4f)
        require(np.array_equal(sv, v4v) and not sc - v4c,
                'Frozen v4 does not preserve indexed source')
        require(sum((v4c - sc).values()) == 4, 'Expected four other v4 fill faces')

        cache = D / 'saved-evaluation-02'
        cache_mesh = cache / 'combined.vmesh'
        cache_facts = inspect_mesh(cache_mesh)
        cached_metrics = json.loads((cache / 'metrics.json').read_text())
        cached_strict = json.loads((cache / 'strict.json').read_text())
        cached_native = json.loads((cache / 'native.json').read_text())
        cache_sha = cache_facts.report['sha256']
        require(cached_metrics['sha256'] == cache_sha == cached_strict['candidate']['sha256'],
                'Cached evidence candidate hash mismatch')
        require(cached_strict['source']['sha256'] == v4facts.report['sha256'],
                'Cached strict evidence uses a different source')
        require(cached_strict['passed'] and cached_strict['conflicts'] == 0 and
                all(cached_strict['checks'].values()) and
                cached_native['conflicts'] == 0 and
                cached_native == cached_metrics['native_audit'], 'Cached audit failed/inconsistent')
        audited = [(cache_facts.oriented_faces, cached_native, cached_strict,
                    {'native': str(cache / 'native.json'), 'strict': str(cache / 'strict.json'),
                     'geometry_sha256': cache_sha})]
        final_facts = None
        final_v = final_f = None
        for name in ('step8_holefill', 'step11_kibble'):
            path = stage(args.obj_root, name)
            facts = inspect_mesh(path)
            v, f = read(path)
            fc = indexed_counter(f)
            require(np.array_equal(sv, v), f'{name}: source vertex array changed')
            require(not sc - fc and not v4c - fc,
                    f'{name}: lost/reoriented source or other v4 fill')
            require(not source_facts.oriented_faces - facts.oriented_faces and
                    not v4facts.oriented_faces - facts.oriented_faces,
                    f'{name}: oriented coordinate multiplicity lost')
            require(len(f) == 5160 and sum((fc - v4c).values()) == 17,
                    f'{name}: expected all 17 replacement faces')
            require(facts.report['exact_duplicate_groups'] == 0 and
                    facts.report['degenerate_faces'] == 0,
                    f'{name}: exact duplicate or degenerate triangle')
            previous = next((entry for entry in audited
                             if entry[0] == facts.oriented_faces), None)
            if previous:
                _, native, strict, provenance = previous
                audit_mode = 'reused_exact_oriented_geometry_multiset'
            else:
                native_path = args.output / f'{name}-native.json'
                strict_path = args.output / f'{name}-strict.json'
                subprocess.run([str(B / 'build/saved_geometry_audit.independent'),
                                str(path), str(native_path),
                                str(args.output / f'{name}-native-pairs.csv'),
                                '1808', '2320', '4112'], check=True)
                native = json.loads(native_path.read_text())
                require(native['conflicts'] == 0, f'{name}: native conflict')
                subprocess.run([sys.executable, str(P / 'exact_patch_intersections.py'),
                                '--source', str(v4path), '--candidate', str(path),
                                '--output', str(strict_path)], check=True)
                strict = json.loads(strict_path.read_text())
                provenance = {'native': str(native_path), 'strict': str(strict_path),
                              'geometry_sha256': facts.report['sha256']}
                audited.append((facts.oriented_faces, native, strict, provenance))
                audit_mode = 'new_geometry_audited'
            require(native['conflicts'] == 0 and strict['passed'] and
                    strict['conflicts'] == 0 and all(strict['checks'].values()),
                    f'{name}: audit did not pass')
            report['stages'][name] = {
                'mesh': facts.report, 'source_5139_preserved': True,
                'other_v4_fill_faces_preserved': 4, 'new_full_fill_faces': 17,
                'audit_mode': audit_mode, 'audit_provenance': provenance,
                'native': native, 'strict_checks': strict['checks'],
                'strict_exact_pairs_checked': strict['exact_pairs_checked'],
                'strict_scope': 'new/v4-source and new/new; unchanged source/source not re-audited'}
            if name == 'step11_kibble':
                final_facts, final_v, final_f = facts, v, f

        fields = ('vertices', 'faces', 'area_voxel2', 'reference_coverage_radius1',
                  'reference_coverage_by_id', 'ct_otsu_supported_area_radius1',
                  'samples', 'source_boundary', 'old_rejected_fill_sample_distance_to_candidate',
                  'new_fill_sample_distance_to_v2_surface')
        if final_facts.oriented_faces == cache_facts.oriented_faces:
            metrics = {key: cached_metrics[key] for key in fields}
            report['metrics_mode'] = 'reused_exact_oriented_geometry_multiset'
            report['metrics_provenance'] = {'path': str(cache / 'metrics.json'),
                                             'sha256': digest(cache / 'metrics.json')}
        else:
            oldpath = stage(B / 'fresh-yplus32-v2/corrected-obj', 'step11_kibble')
            metrics = measure(final_v, final_f, v4v, v4f, oldpath, read, sample)
            report['metrics_mode'] = 'computed_new_geometry'
        report['metrics'] = metrics
        require(metrics['reference_coverage_radius1'] >= 2241,
                'Reference coverage not restored to v2')
        require(metrics['source_boundary']['farther_than1'] == 0,
                'Source boundary points exceed one voxel')
        for key in ('old_rejected_fill_sample_distance_to_candidate',
                    'new_fill_sample_distance_to_v2_surface'):
            require(metrics[key]['max'] <= .25, f'{key}: sample fidelity exceeds .25')
        report['checks']['source_and_other_v4_fill_preserved_in_both_stages'] = True
        report['checks']['both_stages_no_exact_duplicates_degenerates_or_audited_conflicts'] = True
        report['checks']['coverage_restored_and_sample_fidelity_within_quarter'] = True
        report['limitations'] = [
            'Exact strict predicate covers all newly added faces against all v4 faces and each other; source/source strict pairs are not certified.',
            'Finite sample fidelity is not a continuous coverage proof.',
            'CT support, reference proximity and mesh area do not certify anatomical identity or fibers.',
            'Same cube/scroll; broader regression and independent holdout remain separate.']
        report['passed'] = True
    except Exception as exc:
        report['error'] = f'{type(exc).__name__}: {exc}'
    write_json(args.output / 'metrics.json', report)
    print(json.dumps({'passed': report['passed'], 'output': str(args.output),
                      'error': report.get('error')}, indent=2))
    return 0 if report['passed'] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--obj-root', type=Path, default=D / 'full-y32-01-obj')
    parser.add_argument('--log', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=D / 'full-evaluation-01')
    args = parser.parse_args()
    start_guard()
    return evaluate(args)


if __name__ == '__main__':
    raise SystemExit(main())
