"""Guarded saved-core ChartZipper experiment; no extraction or production edits.

Without --calibration, performs the native topology/plane preflight only.
Every invocation requires a fresh --output directory. --build compiles only the
small adapter and links existing libraries. No run or build was done at authoring.
"""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import subprocess
import sys
sys.dont_write_bytecode = True

from prepare_next_validation import ROOT, DEST, require_guard, sha256
from exact_mesh_certificate import inspect_mesh, source_retention
from evaluate_halo_validation import load_arrays, bounded_header, describe

BUILD = ROOT / 'scrollfiesta-comparison/build'
SOURCE = ROOT / 'scrollfiesta-comparison/source/src'
AUDITOR = BUILD / 'saved_geometry_audit.independent'


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def clean_environment():
    return dict(PATH='/usr/bin:/bin', LANG='C', OPENBLAS_NUM_THREADS='1',
                OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', VESUVIUS_THREADS='1',
                OMP_THREAD_LIMIT='1', CUDA_VISIBLE_DEVICES='-1',
                HIP_VISIBLE_DEVICES='-1', ROCR_VISIBLE_DEVICES='', MALLOC_ARENA_MAX='1')


def run(command, log, report):
    report.setdefault('commands', []).append(command)
    with log.open('x') as stream:
        return subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT,
                              env=clean_environment(), check=False).returncode


def calibration(path, out, frozen):
    data = json.loads(path.read_text())
    if (data.get('calibration_valid') is not True or
            data.get('winding_gate_ready') is not True):
        raise ValueError('Calibration is not validated and ready for the winding gate; diagnostic values cannot arm a weld')
    if data['source_sha256'] != frozen['source_sha256'] or data['coordinates'] != 'worldZYX':
        raise ValueError('Calibration must refer to the exact frozen CT and worldZYX frame')
    if not data.get('provenance') or not data.get('pitch_method'):
        raise ValueError('Calibration needs axis provenance and measured pitch method/uncertainty')
    if not data.get('pitch_uncertainty_voxels'):
        raise ValueError('Supply a documented pitch uncertainty interval, not an invented scalar')
    pitch = float(data['pitch_voxels'])
    lo, hi = map(float, data['pitch_uncertainty_voxels'])
    if not all(map(math.isfinite, (pitch, lo, hi))) or not 0 < lo <= pitch <= hi:
        raise ValueError('Invalid pitch or uncertainty interval')
    rows = data['axis_zyx']
    if not 2 <= len(rows) <= 4096:
        raise ValueError('Expected 2..4096 documented axis samples')
    for i, row in enumerate(rows):
        if len(row) != 3 or not all(math.isfinite(float(x)) for x in row):
            raise ValueError('Invalid axis sample')
        if i and float(row[0]) <= float(rows[i-1][0]):
            raise ValueError('Axis samples must have strictly increasing world Z')
    if float(rows[0][0]) > 1888 or float(rows[-1][0]) < 1920:
        raise ValueError('Axis samples must cover the active ROI Z interval 1888..1920')
    for item in data['provenance']:
        if sha256(Path(item['path'])) != item['sha256']:
            raise ValueError('Calibration provenance evidence changed')
    native = out / 'calibration.native.txt'
    with native.open('x') as stream:
        stream.write(f'{pitch:.17g} {len(rows)}\n')
        for row in rows:
            stream.write(' '.join(format(float(x), '.17g') for x in row) + '\n')
    save(out / 'calibration.json', data)
    return native


def band_and_connectivity(v, f, before, lv, lf, rv, rf):
    """Fixed initial sample IDs; report closure separately from distances."""
    import numpy as np
    from independent_split_common import point_to_triangles
    edges = Counter(tuple(sorted((int(a), int(b))))
                    for t in f for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])))
    open_vertices = {a for edge, n in edges.items() if n == 1 for a in edge}
    bridge = f[len(lf)+len(rf):]
    directions = {}
    for side, offset, other_v, other_f in (('left', 0, rv, rf), ('right', len(lv), lv, lf)):
        key = side + '_to_' + ('right' if side == 'left' else 'left')
        baseline = before['directions'][key]
        ids = [i + offset for i in baseline['sample_vertex_indices']]
        remaining = [i for i in ids if i in open_vertices]
        target = other_v[other_f].astype('float64')
        if len(bridge):
            target = np.concatenate((target, v[bridge].astype('float64')))
        distances = np.array([float(point_to_triangles(target, v[i].astype('float64')).min())
                              for i in remaining])
        directions[key] = {'original_samples': len(ids), 'remaining_open_samples': len(remaining),
            'closed_samples': len(ids)-len(remaining), 'remaining_global_vertex_ids': remaining,
            'remaining_to_other_source_plus_bridge': describe(distances),
            'remaining_distance_gt4': int(np.count_nonzero(distances > 4)),
            'distance_meaning': 'Geometry only; bridge distance may be zero at an incident bridge. Not anatomical correspondence.'}
    # Source component membership after welding, with no coordinate-based unions.
    parent = list(range(len(v)))
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for t in f:
        for b in (t[1], t[2]):
            parent[find(int(b))] = find(int(t[0]))
    groups = {}
    for i, t in enumerate(f):
        root = find(int(t[0]))
        g = groups.setdefault(root, dict(left_source_faces=0, right_source_faces=0, bridge_faces=0))
        name = 'left_source_faces' if i < len(lf) else 'right_source_faces' if i < len(lf)+len(rf) else 'bridge_faces'
        g[name] += 1
    return {'directions': directions, 'indexed_component_membership': list(groups.values()),
            'mixed_core_components': sum(bool(g['left_source_faces'] and g['right_source_faces']) for g in groups.values()),
            'source_to_opposite_source_distances_unchanged_if_exact_retention': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--build', action='store_true')
    parser.add_argument('--binary', type=Path)
    parser.add_argument('--calibration', type=Path)
    args = parser.parse_args()
    guarded = require_guard()  # Before numeric imports, hashing or compilation.
    out = args.output.resolve()
    if ROOT not in out.parents:
        raise ValueError('Output must be a fresh directory inside this research project')
    out.mkdir()
    report = {'guard': guarded, 'status': 'started', 'accepted': False,
              'anatomical_identity_certified': False, 'commands': []}
    try:
        frozen = json.loads((DEST / 'frozen-input.json').read_text())
        evaluation = json.loads((DEST / 'evaluation-v2/results.json').read_text())
        if not evaluation['passed'] or frozen['expected_trim_planes_world_x'] != [4175, 4177]:
            raise ValueError('Frozen baseline is not the expected passing halo experiment')
        report['baseline_results_sha256'] = sha256(DEST / 'evaluation-v2/results.json')
        report['frozen_input_sha256'] = sha256(DEST / 'frozen-input.json')
        report['code_and_library_sha256'] = {str(p): sha256(p) for p in (
            Path(__file__), ROOT/'saved_core_weld.c', BUILD/'libscrollfiesta_core.a',
            SOURCE/'remesh/chart_zipper.c', SOURCE/'remesh/seam_planes.c',
            SOURCE/'flatten/topology_invariants.c', AUDITOR)}
        records = [evaluation['cases']['v4-'+s]['stages']['step12_final'] for s in ('left', 'right')]
        union = evaluation['unions']['v4']
        for record in records + [union]:
            path = Path(record['path'])
            bounded_header(path)
            if sha256(path) != record['sha256']:
                raise ValueError('Frozen saved geometry changed')
        for side in ('left', 'right'):
            entry = frozen['inputs'][side]
            if sha256(DEST / entry['stdin_file']) != entry['stdin_sha256']:
                raise ValueError('Frozen prediction changed')
        if sha256(AUDITOR) != evaluation['provenance']['auditor_sha256']:
            raise ValueError('Baseline audit reuse requires the identical auditor')
        report['inputs'] = records
        report['before_audit_reused'] = union['audit']
        report['band_before_reused'] = evaluation['seams']['v2']
        binary = args.binary.resolve() if args.binary else out/'saved_core_weld'
        if args.build:
            if args.binary:
                raise ValueError('--build creates a new isolated binary; do not supply --binary')
            obj = out/'saved_core_weld.o'
            commands = [
                ['/usr/bin/cc', '-std=c11', '-O1', '-Wall', '-Wextra', '-I'+str(SOURCE),
                 '-c', str(ROOT/'saved_core_weld.c'), '-o', str(obj)],
                ['/usr/bin/c++', str(obj), str(BUILD/'libscrollfiesta_core.a'),
                 str(BUILD/'libsf_triangle.a'), str(BUILD/'clipper2/libClipper2.a'),
                 str(BUILD/'clipper2/libClipper2Z.a'), '-fopenmp', '-lm', '/lib64/libtiff.so.6', '-o', str(binary)]]
            for i, command in enumerate(commands):
                if run(command, out/f'build-{i}.log', report):
                    raise RuntimeError('Isolated adapter compilation/link failed; see preserved log')
        if not binary.is_file():
            raise ValueError('Supply --build or an existing --binary')
        report['binary_sha256'] = sha256(binary)
        command = [str(binary), union['path'], str(out/'candidate.vmesh'), str(out/'native.json')]
        if args.calibration:
            command.append(str(calibration(args.calibration, out, frozen)))
        rc = run(command, out/'native.log', report)
        report['native_returncode'] = rc
        if (out/'native.json').exists():
            report['native'] = json.loads((out/'native.json').read_text())
        if rc == 4:
            report['status'] = 'preflight_only_or_blocked'
            report['blockers'] = []
            native = report['native']
            if not args.calibration:
                report['blockers'].append('Missing same-CT axis/pitch calibration; physical weld not attempted')
            if not native['before']['all_disks'] or native['before']['inconsistent_winding']:
                report['blockers'].append('Source charts do not meet unchanged grid_weld disk/winding precondition')
            if not native['plane_world_x_4176_verified']:
                report['blockers'].append('Seam plane detector did not find exactly the expected X=4176 plane')
            return 2
        if rc:
            raise RuntimeError('Native adapter failed; partial evidence retained')
        candidate = out/'candidate.vmesh'
        bounded_header(candidate)
        source_facts, after_facts = inspect_mesh(Path(union['path'])), inspect_mesh(candidate)
        report['exact_source_retention'] = source_retention(source_facts, after_facts)
        report['after_exact'] = after_facts.report
        if run([str(AUDITOR), str(candidate), str(out/'audit.json'), str(out/'pairs.csv'),
                '1840', '2320', '4048'], out/'audit.log', report):
            raise RuntimeError('Independent all-triangle 3D audit failed')
        audit = json.loads((out/'audit.json').read_text())
        if (audit['predicate_fixture_checks'] != 4 or not audit['include_hinges'] or
            audit['gap_max'] != 0 or audit['faces'] != after_facts.report['faces']):
            raise ValueError('Independent auditor contract mismatch')
        report['after_audit'] = audit
        lv, lf = load_arrays(Path(records[0]['path']))
        rv, rf = load_arrays(Path(records[1]['path']))
        v, f = load_arrays(candidate)
        import numpy as np
        triangles = v[f].astype('float64')
        report['area_voxel2'] = {
            'before': union['area_voxel2'],
            'after': float((np.linalg.norm(np.cross(triangles[:, 1]-triangles[:, 0],
                                                  triangles[:, 2]-triangles[:, 0]), axis=1)/2).sum())}
        report['area_voxel2']['delta'] = report['area_voxel2']['after'] - union['area_voxel2']
        del triangles
        report['after_band_and_connectivity'] = band_and_connectivity(
            v, f, evaluation['seams']['v2'], lv, lf, rv, rf)
        n = report['native']
        report['accepted'] = bool(report['exact_source_retention']['retained'] and
            not after_facts.report['duplicate_extra_faces'] and not after_facts.report['degenerate_faces'] and
            not audit['conflicts'] and n['gate_armed'] and n['source_prefix_exact'] and
            n['embedded_certificate'] and n['after']['all_disks'] and
            not n['after']['inconsistent_winding'] and not n['orientation_residual'] and
            n['after']['components'] + n['accepted_transactions'] == n['before']['components'])
        report['continuity_improved_geometrically'] = bool(report['accepted'] and
            n['bridge_faces'] > 0 and report['after_band_and_connectivity']['mixed_core_components'] > 0)
        report['status'] = 'geometrically_accepted' if report['accepted'] else 'rejected_candidate_preserved'
        return 0 if report['accepted'] else 1
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        report['status'] = 'failed'
        report['error'] = str(error)
        return 1
    finally:
        save(out/'report.json', report)
        print(json.dumps({'report': str(out/'report.json'), 'status': report['status'],
                          'accepted': report['accepted']}), flush=True)


if __name__ == '__main__':
    raise SystemExit(main())
