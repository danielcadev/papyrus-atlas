"""Sequential v5 regressions; reuse evidence only for identical frozen meshes.

Invoke through run_holefill_guarded.sh. A geometric difference stops the run
and requires a separate exact audit; no native-only fallback certifies it.
"""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

from guard import start_guard


ROOT = Path(__file__).resolve().parent
BASE = ROOT / 'scrollfiesta-comparison'
DEST = BASE / 'hole-recovery-v5/regressions-v5-01'
FROZEN = BASE / 'holefill-repair-v4'
BINARY = BASE / 'build/cube_mesh.holefill-v5'
GUARD_OK = 'Guard: 0 NM-edge(s) (-0 faces), 0 pinch split(s), 0 reorient flip(s)'


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def identical(left, right):
    if left.stat().st_size != right.stat().st_size:
        return False
    with left.open('rb') as a, right.open('rb') as b:
        while True:
            block = a.read(1024 * 1024)
            if block != b.read(1024 * 1024):
                return False
            if not block:
                return True


def stage(folder, name):
    files = list(folder.glob(f'*/*{name}/*_all.vmesh'))
    assert len(files) == 1, f'Expected exactly one {name} in {folder}: {files}'
    return files[0]


def write_new(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def main():
    start_guard()
    assert not DEST.exists(), f'Preserve previous run: {DEST}'
    assert os.environ.get('VESUVIUS_THREADS') == '1'
    assert os.environ.get('OMP_THREAD_LIMIT') == '1'
    frozen_report_path = FROZEN / 'regressions.json'
    frozen_report = json.loads(frozen_report_path.read_text())
    env = os.environ.copy()
    for key in ('MLS_RADIUS_VOX', 'MLS_PERTURB_EPS'):
        env.pop(key, None)
    env.update(MLS_EDGE_ADAPT='soft', VES_OVERLAP_COVERAGE_GUARD='1',
               VES_HOLE_RECOVERY_SEARCH='1')
    binary_sha = digest(BINARY)
    cases = [
        ('central', BASE / 'independent-central32/cubes_PRED/z01808_y02320_x04112.tif',
         BASE / 'independent-central32/v2-obj',
         BASE / 'independent-central32/v2-native-geometry.json',
         BASE / 'independent-central32/v2-evaluation.json'),
        ('xplus32', BASE / 'independent-xplus32/cubes_PRED/z01808_y02320_x04112.tif',
         BASE / 'independent-xplus32/v2-obj',
         BASE / 'independent-xplus32/corrected-native-geometry.json',
         BASE / 'independent-xplus32/v2-evaluation.json'),
        ('original', BASE / 'inputs/adaptive8-taper3/cubes_PRED/z00768_y02408_x03536.tif',
         BASE / 'boundary-graft-soft-obj',
         BASE / 'boundary-graft-soft-native-geometry.json',
         BASE / 'boundary-graft-soft-evaluation.json'),
    ]
    plan = {}
    # Freeze every reference and input before starting the first mesher.
    for name, input_file, v2_folder, audit, metrics in cases:
        frozen = frozen_report[name]
        v4_folder = FROZEN / f'{name}-obj'
        v4_final = stage(v4_folder, 'step11_kibble')
        v2_final = stage(v2_folder, 'step11_kibble')
        v4_source = stage(v4_folder, 'step7_cc_bpa')
        v2_source = stage(v2_folder, 'step7_cc_bpa')
        assert frozen['byte_identical_to_v2'] and frozen['guard_changes'] == 0
        assert digest(input_file) == frozen['input_sha256'], f'Changed input: {name}'
        assert digest(v4_final) == frozen['final_sha256'], f'Changed frozen v4: {name}'
        assert identical(v4_final, v2_final), f'Frozen v4/v2 final mismatch: {name}'
        assert identical(v4_source, v2_source), f'Frozen v4/v2 step7 mismatch: {name}'
        assert json.loads(audit.read_text())['conflicts'] == 0
        plan[name] = dict(input=str(input_file), input_sha256=frozen['input_sha256'],
                          v4_final=str(v4_final), v2_final=str(v2_final),
                          final_sha256=frozen['final_sha256'],
                          v4_source=str(v4_source), v2_source=str(v2_source),
                          source_sha256=digest(v4_source), native_audit=str(audit),
                          native_audit_sha256=digest(audit), metrics=str(metrics),
                          metrics_sha256=digest(metrics))
    DEST.mkdir(parents=True)
    write_new(DEST / 'plan.json', dict(binary=str(BINARY), binary_sha256=binary_sha,
              script_sha256=digest(Path(__file__)),
              frozen_v4_report=str(frozen_report_path), frozen_v4_report_sha256=digest(frozen_report_path),
              environment={key: env[key] for key in ('MLS_EDGE_ADAPT', 'VES_OVERLAP_COVERAGE_GUARD',
                                                    'VES_HOLE_RECOVERY_SEARCH')}, cases=plan,
              changed_geometry_policy='Stop; require exact independent audit plus native audit before accepting'))
    results = {}
    active_name = None
    try:
        for name, input_file, _, _, _ in cases:
            active_name = name
            record = plan[name]
            folder = DEST / name
            folder.mkdir()
            output = folder / 'obj'
            log = folder / 'meshing.log'
            command = [str(BINARY), str(input_file), str(folder / 'output.tif'),
                       '--dump-obj', str(output), '--no-simplify']
            assert digest(BINARY) == binary_sha, 'v5 binary changed during regressions'
            assert digest(input_file) == record['input_sha256'], 'Input changed during regressions'
            write_new(folder / 'command.json', dict(command=command, binary_sha256=binary_sha,
                      VES_HOLE_RECOVERY_SEARCH='1', MLS_EDGE_ADAPT='soft', VES_OVERLAP_COVERAGE_GUARD='1'))
            with log.open('x') as stream:
                subprocess.run(command, env=env, stdout=stream, stderr=subprocess.STDOUT, check=True)
            text = log.read_text()
            statuses = [line for line in text.splitlines() if 'Status:' in line]
            guards = [line for line in text.splitlines() if 'Guard:' in line]
            assert statuses and all('Status: OK' in line for line in statuses), f'Pipeline not OK: {name}'
            assert guards and all(GUARD_OK in line for line in guards), f'Nonzero guard: {name}'
            source = stage(output, 'step7_cc_bpa')
            final = stage(output, 'step11_kibble')
            source_same = (digest(source) == record['source_sha256'] and
                           identical(source, Path(record['v4_source'])) and
                           identical(source, Path(record['v2_source'])))
            final_same = (digest(final) == record['final_sha256'] and
                          identical(final, Path(record['v4_final'])) and
                          identical(final, Path(record['v2_final'])))
            outcome = dict(command=command, input_sha256=record['input_sha256'],
                           final=str(final), final_sha256=digest(final),
                           source_sha256=digest(source), step7_byte_identical_to_frozen=source_same,
                           byte_identical_to_v4=final_same, byte_identical_to_v2=final_same,
                           guard_changes=0, status_ok=True)
            if not source_same or not final_same:
                outcome.update(state='blocked_exact_audit_required',
                    reason='Changed saved geometry: require exact oriented source-preservation and duplicate/intersection audit; native-only audit is insufficient',
                    prior_native_audit_reused=False, success=False)
                write_new(folder / 'exact-audit-required.json', outcome)
                write_new(DEST / 'blocked.json', dict(case=name, completed_cases=results, **outcome))
                print(json.dumps(outcome), flush=True)
                return 2
            # Historical audit/metric artifacts must still match their preflight hashes.
            for path_key, hash_key in [('native_audit', 'native_audit_sha256'), ('metrics', 'metrics_sha256')]:
                assert digest(Path(record[path_key])) == record[hash_key], f'Frozen evidence changed: {name}'
            outcome.update(state='byte-identical', prior_native_audit_reused=True,
                           native_geometry_reused_from=record['native_audit'],
                           metrics_reused_from=record['metrics'], frozen_provenance=record)
            write_new(folder / 'result.json', outcome)
            results[name] = outcome
            print(name, 'byte-identical to frozen v4/v2; step7 identical; saved audit/metrics reused', flush=True)
    except Exception as error:
        write_new(DEST / 'failed.json', dict(case=active_name, error=str(error),
                  completed_cases=results, success=False, incomplete=True))
        raise
    write_new(DEST / 'regressions.json', dict(success=True, binary_sha256=binary_sha,
              VES_HOLE_RECOVERY_SEARCH='1', all_step7_frozen_identical=True,
              all_finals_byte_identical_to_v4_v2=True, cases=results))
    return 0


if __name__ == '__main__':
    sys.exit(main())
