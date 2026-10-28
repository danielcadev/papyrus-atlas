"""Evaluate the frozen +32Z halo fixture; execute only under the guarded runner.

All outputs are exclusive under evaluation-v2. No meshing, labels, or retuning.
Exact certificates use stdlib; NumPy is imported only after require_guard().
"""
from collections import Counter
import csv
import json
from pathlib import Path
import pickle
import re
import struct
import subprocess

from exact_mesh_certificate import MeshFacts, inspect_mesh, source_retention
from prepare_next_validation import DEST, ROOT, require_guard, sha256

OUT = DEST / 'evaluation-v2'
AUDITOR = ROOT / 'scrollfiesta-comparison/build/saved_geometry_audit.independent'
ORIGIN = [1840, 2320, 4048]
STAGES = ('step7_cc_bpa', 'step8_holefill', 'step11_kibble', 'step12_final')
GUARD = re.compile(r'Guard:\s*(\d+) NM-edge\(s\) \(-([0-9]+) faces\),\s*'
                   r'(\d+) pinch split\(s\),\s*(\d+) reorient flip\(s\)')
GUARD_KEYS = ('nonmanifold_edges', 'removed_faces', 'pinch_splits', 'reorient_flips')
HEADER = struct.Struct('<8sIIIIQQQQQ')


def save(path, record):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(record, stream, indent=2, allow_nan=False)
        stream.write('\n')


def load_arrays(path):
    """Already certified, bounded VMESH; retain global ZYX, including for union."""
    import numpy as np
    data = path.read_bytes()
    h = HEADER.unpack_from(data)
    nv, nf, vo, _, fo = h[5:]
    v = np.frombuffer(data, dtype='<f4', count=nv * 3, offset=vo).reshape(nv, 3)
    f = np.frombuffer(data, dtype='<i4', count=nf * 3, offset=fo).reshape(nf, 3)
    return v, f


def bounded_header(path):
    with path.open('rb') as stream:
        h = HEADER.unpack(stream.read(HEADER.size))
    # These are evaluation resource bounds, not geometric acceptance criteria.
    if h[5] > 100000 or h[6] > 50000:
        raise ValueError(f'{path}: fixture exceeds evaluator bound (100k vertices/50k faces)')
    return h


class GeometryCache:
    def __init__(self):
        self.metrics = {}
        self.audits = {}
        self.retention = {}

    def inspect(self, path):
        digest = sha256(path)
        reused = digest in self.metrics
        if not reused:
            h = bounded_header(path)
            if h[5] == 0 or h[6] == 0:
                raise ValueError(f'{path}: empty mesh is an explicit failed outcome; no audit inferred')
            facts = inspect_mesh(path)
            import numpy as np
            v, f = load_arrays(path)
            tri = v[f].astype('float64')
            area = float((np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0],
                                                 tri[:, 2] - tri[:, 0]), axis=1) / 2).sum())
            facts.report['area_voxel2'] = area
            metrics_file = OUT / (digest + '-exact.json')
            save(metrics_file, facts.report)
            # Only this process creates/reads these private cache files. Disk
            # storage avoids retaining every mesh's coordinate Counter in RAM.
            with (OUT / (digest + '-directed.pkl')).open('xb') as stream:
                pickle.dump(facts.oriented_faces, stream, protocol=4)
            self.metrics[digest] = facts.report
        record = self.metrics[digest]
        return {'path': str(path), 'sha256': digest,
                'metrics_file': str(OUT / (digest + '-exact.json')),
                'reused_identical_geometry': reused,
                'first_geometry_path': record['path'],
                **{key: record[key] for key in ('vertices', 'faces', 'area_voxel2',
                    'exact_duplicate_groups', 'duplicate_extra_faces', 'degenerate_faces')}}

    def facts(self, digest):
        with (OUT / (digest + '-directed.pkl')).open('rb') as stream:
            return MeshFacts(self.metrics[digest], pickle.load(stream))

    def source_check(self, before, after):
        key = (before['sha256'], after['sha256'])
        reused = key in self.retention
        if not reused:
            self.retention[key] = source_retention(self.facts(key[0]), self.facts(key[1]))
        return dict(self.retention[key], reused_identical_geometry=reused)

    def audit(self, mesh):
        digest = mesh['sha256']
        reused = digest in self.audits
        if not reused:
            path = Path(mesh['path'])
            result_file = OUT / (digest + '-audit.json')
            pairs_file = OUT / (digest + '-pairs.csv')
            if result_file.exists() or pairs_file.exists():
                raise FileExistsError('Refusing to overwrite native audit output')
            command = [str(AUDITOR), str(path), str(result_file), str(pairs_file), *map(str, ORIGIN)]
            with (OUT / (digest + '-audit.log')).open('x') as stream:
                subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, check=True)
            record = json.loads(result_file.read_text())
            if (record.get('predicate_fixture_checks') != 4 or record.get('gap_max') != 0
                    or record.get('include_hinges') is not True or record.get('read_only') is not True
                    or record.get('faces') != mesh['faces']):
                raise ValueError('Native audit contract mismatch')
            v, f = load_arrays(path)
            signatures = Counter()
            with pairs_file.open() as stream:
                for row in csv.DictReader(stream):
                    a, b, kind = (int(row[k]) for k in ('face0', 'face1', 'kind'))
                    if not (0 <= a < len(f) and 0 <= b < len(f)):
                        raise ValueError('Audit pair has an invalid face index')
                    triangles = [sorted(tuple(float(x) if x != 0 else 0.0 for x in p)
                                        for p in v[f[index]]) for index in (a, b)]
                    # IDs may change: compare exact global geometry and kind.
                    signature = json.dumps([kind, sorted(triangles)], separators=(',', ':'))
                    signatures[signature] += 1
            if sum(signatures.values()) != record['conflicts']:
                raise ValueError('Native audit pair count disagrees with summary')
            self.audits[digest] = dict(summary=record, signatures=signatures,
                                      result_file=str(result_file), pairs_file=str(pairs_file),
                                      command=command)
        record = self.audits[digest]
        return dict(summary=record['summary'], result_file=record['result_file'],
                    pairs_file=record['pairs_file'], command=record['command'],
                    reused_identical_geometry=reused)


def stage_path(folder, stage):
    # The pipeline also publishes all_obj mirror copies. Select the canonical
    # stage directory, rather than counting those mirrors as extra meshes.
    files = list(folder.glob(f'*/*{stage}/*{stage}_all.vmesh'))
    if len(files) != 1:
        raise ValueError(f'{folder}: expected one {stage} mesh, found {len(files)}; empty/missing output retained')
    return files[0]


def log_record(name, case):
    launch_name = case['guarded_launch'][2]
    log_path = ROOT / 'native' / (launch_name + '.log')
    status_path = ROOT / 'native' / (launch_name + '.status.json')
    text = log_path.read_text()
    status = json.loads(status_path.read_text())
    finished = json.loads((DEST / (name + '-finished.json')).read_text())
    guards = [dict(zip(GUARD_KEYS, map(int, match))) for match in GUARD.findall(text)]
    guard_lines = [line for line in text.splitlines() if re.search(r'\bGuard:', line)]
    statuses = re.findall(r'Status:\s*(\S+)', text)
    valid = (statuses and all(item == 'OK' for item in statuses) and guards
             and len(guards) == len(guard_lines) and status['returncode'] == 0
             and status['reason'] == 'completed' and finished['returncode'] == 0)
    return {'valid': bool(valid), 'log': str(log_path), 'runner_status': status,
            'finished': finished, 'pipeline_statuses': statuses, 'guards': guards,
            'guard_lines': guard_lines,
            'guard_totals': {k: sum(g[k] for g in guards) for k in GUARD_KEYS},
            'trim_lines': [line for line in text.splitlines() if 'trim' in line.lower()],
            'timing_lines': [line for line in text.splitlines() if 'Timings:' in line],
            'cgroup_memory_peak_bytes': None,
            'memory_note': 'Runner records max_child_rss_mib, not cgroup memory.peak; no peak invented.'}


def make_union(version, left, right):
    import numpy as np
    lv, lf = load_arrays(Path(left['path']))
    rv, rf = load_arrays(Path(right['path']))
    nv, nf = len(lv) + len(rv), len(lf) + len(rf)
    if nv >= 2**31:
        raise ValueError('Union indices exceed int32')
    path = OUT / (version + '-union-final-global-zyx.vmesh')
    with path.open('xb') as stream:
        stream.write(HEADER.pack(b'VESMESH1', 1, 0x01020304, 0, 64,
                                 nv, nf, 64, 0, 64 + nv * 12))
        stream.write(lv.astype('<f4', copy=False).tobytes())
        stream.write(rv.astype('<f4', copy=False).tobytes())
        stream.write(lf.astype('<i4', copy=False).tobytes())
        stream.write((rf.astype('int64') + len(lv)).astype('<i4').tobytes())
    return path


def describe(values):
    if not len(values):
        return {'count': 0, 'min': None, 'mean': None, 'median': None, 'p95': None, 'max': None}
    import numpy as np
    return {'count': len(values), 'min': float(np.min(values)), 'mean': float(np.mean(values)),
            'median': float(np.median(values)), 'p95': float(np.percentile(values, 95)),
            'max': float(np.max(values))}


def seam_metrics(left, right):
    import numpy as np
    from independent_split_common import point_to_triangles
    meshes = [load_arrays(Path(item['path'])) for item in (left, right)]
    directions = {}
    for index, (side, plane) in enumerate((('left', 4175), ('right', 4177))):
        v, f = meshes[index]
        edges = Counter(tuple(sorted((int(a), int(b))))
                        for t in f for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])))
        boundary = [edge for edge, count in edges.items() if count == 1]
        vertices = sorted({i for edge in boundary for i in edge})
        selected = [i for i in vertices if abs(float(v[i, 2]) - plane) <= 4]
        samples = v[selected].astype('float64')
        plane_distances = np.abs(samples[:, 2] - plane)
        other_v, other_f = meshes[1 - index]
        triangles = other_v[other_f].astype('float64')
        # One sample at a time; no samples-by-all-triangles matrix.
        distances = np.array([float(point_to_triangles(triangles, p).min()) for p in samples])
        directions[side + '_to_' + ('right' if index == 0 else 'left')] = {
            'expected_plane_world_x': plane, 'boundary_edges_total': len(boundary),
            'boundary_vertices_total': len(vertices), 'band_sample_vertices': len(selected),
            'empty_band': not selected, 'distance_to_expected_plane': describe(plane_distances),
            'point_to_other_core_triangles': describe(distances),
            'unmatched_threshold_voxels_exclusive': 4,
            'unmatched_count': int(np.count_nonzero(distances > 4)),
            'unmatched_fraction': float(np.mean(distances > 4)) if len(distances) else None,
            'unmatched_fraction_reason': 'empty boundary band' if not selected else None,
            'sample_vertex_indices': selected}
    return {'directions': directions, 'band_width_voxels': 4,
            'sampling': 'Every indexed vertex incident to an edge with exactly one face, within inclusive |worldX-plane|<=4; no subsampling or coordinate welding',
            'target': 'All triangles of the other final owned core; directed metrics reported in both directions',
            'expected_gap_voxels': 2,
            'interpretation': 'Descriptive distances include intentional gap2; no weld, sheet identity, or final-cut activation certificate'}


def duplicate_counter(report):
    return Counter({json.dumps(group['global_zyx_vertices'], separators=(',', ':')):
                    len(group['face_indices']) - 1 for group in report['duplicate_groups']})


def compare(cache, before, after, audited=True):
    b, a = before['sha256'], after['sha256']
    new_duplicates = duplicate_counter(cache.metrics[a]) - duplicate_counter(cache.metrics[b])
    new_pairs = (cache.audits[a]['signatures'] - cache.audits[b]['signatures']) if audited else Counter()
    return {'byte_identical': a == b, 'faces_delta': after['faces'] - before['faces'],
            'area_delta_voxel2': after['area_voxel2'] - before['area_voxel2'],
            'new_duplicate_extra_faces': sum(new_duplicates.values()),
            'new_duplicate_geometries': [{'global_zyx_vertices': json.loads(k), 'extra_faces': v}
                                         for k, v in new_duplicates.items()],
            'new_conflict_pairs': sum(new_pairs.values()),
            'new_conflict_geometry': [{'kind_and_triangles': json.loads(k), 'multiplicity': v}
                                      for k, v in new_pairs.items()],
            'no_new_conflicts_or_duplicates': not new_duplicates and not new_pairs,
            'audited_pair_comparison': audited}


def main():
    guarded = require_guard()
    OUT.mkdir()  # Exclusive: failure/partial output is evidence, never overwritten.
    report = {'experiment': DEST.name, 'guard': guarded, 'cases': {}, 'comparisons': {},
              'unions': {}, 'seams': {}, 'failures': [], 'passed': False}
    cache = GeometryCache()
    try:
        frozen = json.loads((DEST / 'frozen-input.json').read_text())
        expected = {'v2-left', 'v2-right', 'v4-left', 'v4-right'}
        if set(frozen['cases']) != expected:
            raise ValueError('Frozen fixture must contain exactly the four declared cases')
        if (sha256(ROOT / 'prepare_next_validation.py') != frozen['preparer_sha256']
                or sha256(DEST / 'run_case.py') != frozen['runner_sha256']):
            raise ValueError('Frozen preparer/runner changed')
        if (frozen['expected_trim_planes_world_x'] != [4175, 4177]
                or frozen['expected_gap_voxels'] != 2):
            raise ValueError('Frozen seam coordinates differ from the declared protocol')
        report['provenance'] = {'frozen_input_sha256': sha256(DEST / 'frozen-input.json'),
            'evaluator_sha256': sha256(Path(__file__)), 'auditor_sha256': sha256(AUDITOR),
            'exact_certificate_sha256': sha256(ROOT / 'exact_mesh_certificate.py'),
            'point_triangle_helper_sha256': sha256(ROOT / 'independent_split_common.py')}
        report['limitations'] = frozen['limitations'] + [
            'No manual labels opened by evaluator. Same CT cube/scroll; not independent holdout.',
            'Union is concatenated final meshes without welding or coordinate translation.',
            'Do not combine pretrim halos: their overlap is intentional.',
            'No final triangle-cut activation claimed; inspect trim_lines and pre-BPA owned trim.',
            'Exact duplicate and native intersection audits do not certify anatomical identity.']
        for name in ('v2-left', 'v2-right', 'v4-left', 'v4-right'):
            case = frozen['cases'][name]
            entry = {'stages': {}}
            report['cases'][name] = entry
            try:
                if (sha256(Path(case['binary'])) != case['binary_sha256']
                        or sha256(DEST / case['stdin_file']) != case['stdin_sha256']):
                    raise ValueError('Frozen binary/input changed')
                entry['execution'] = log_record(name, case)
                if not entry['execution']['valid']:
                    report['failures'].append(name + ': missing Status OK, complete guards or successful exits')
                for stage in STAGES:
                    mesh = cache.inspect(stage_path(Path(case['output_directory']), stage))
                    entry['stages'][stage] = mesh
                    if stage in ('step11_kibble', 'step12_final'):
                        mesh['audit'] = cache.audit(mesh)
                entry['source_retention_step7_to_step8'] = cache.source_check(
                    entry['stages']['step7_cc_bpa'], entry['stages']['step8_holefill'])
                if not entry['source_retention_step7_to_step8']['retained']:
                    report['failures'].append(name + ': source missing or reoriented at holefill')
            except (OSError, ValueError, KeyError, struct.error, subprocess.CalledProcessError) as error:
                entry['error'] = str(error)
                report['failures'].append(name + ': ' + str(error))

        for side in ('left', 'right'):
            before, after = (report['cases'][v + '-' + side] for v in ('v2', 'v4'))
            if 'error' in before or 'error' in after:
                continue
            comparisons = {}
            report['comparisons'][side] = comparisons
            bs, aas = before['stages'], after['stages']
            same_source = (Path(bs['step7_cc_bpa']['path']).read_bytes()
                           == Path(aas['step7_cc_bpa']['path']).read_bytes())
            comparisons['step7_byte_identical'] = same_source
            if not same_source:
                report['failures'].append(side + ': v2/v4 prefill source bytes differ')
            bg, ag = before['execution']['guards'], after['execution']['guards']
            guard_ok = len(bg) == len(ag) and all(a[k] <= b[k] for a, b in zip(ag, bg) for k in GUARD_KEYS)
            comparisons['guards_no_increased_counter'] = guard_ok
            if not guard_ok:
                report['failures'].append(side + ': v4 guard count/counters differ adversely')
            for stage in ('step8_holefill', 'step11_kibble', 'step12_final'):
                result = compare(cache, bs[stage], aas[stage], audited=stage != 'step8_holefill')
                comparisons[stage] = result
                if not result['no_new_conflicts_or_duplicates']:
                    report['failures'].append(side + '/' + stage + ': new v4 conflict or duplicate geometry')

        seam_cache = {}
        for version in ('v2', 'v4'):
            left, right = (report['cases'][version + '-' + side] for side in ('left', 'right'))
            if 'error' in left or 'error' in right:
                report['seams'][version] = {'omitted_reason': 'Incomplete or empty core output; see case errors'}
                continue
            lm, rm = left['stages']['step12_final'], right['stages']['step12_final']
            union = cache.inspect(make_union(version, lm, rm))
            union['audit'] = cache.audit(union)
            report['unions'][version] = union
            key = (lm['sha256'], rm['sha256'])
            if key in seam_cache:
                report['seams'][version] = {'reused_from_version': seam_cache[key],
                                           'reason': 'Both final core VMESH hashes identical'}
            else:
                report['seams'][version] = seam_metrics(lm, rm)
                seam_cache[key] = version
        if set(report['unions']) == {'v2', 'v4'}:
            result = compare(cache, report['unions']['v2'], report['unions']['v4'])
            report['comparisons']['union_final'] = result
            if not result['no_new_conflicts_or_duplicates']:
                report['failures'].append('union_final: new v4 conflict or duplicate geometry')
        report['cache'] = {'unique_meshes_certified': len(cache.metrics),
                           'unique_meshes_native_audited': len(cache.audits),
                           'audit_origin_world_zyx': ORIGIN,
                           'policy': 'SHA256 of entire VMESH, fixed auditor/options/origin; identical hashes reuse exact metrics and audits'}
    except (OSError, ValueError, KeyError, struct.error, subprocess.CalledProcessError) as error:
        report['failures'].append(type(error).__name__ + ': ' + str(error))
    report['passed'] = not report['failures']
    save(OUT / 'results.json', report)
    print(json.dumps({'results': str(OUT / 'results.json'), 'passed': report['passed'],
                      'failures': report['failures']}), flush=True)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
