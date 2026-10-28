"""Run frozen halo cores with v5/search ON; accept only exact v4 parity.

Use run_holefill_guarded.sh. This does not generate or reinterpret geometry
audits: identical saved stages reuse evaluation-v2; any change stops the run.
"""
from pathlib import Path
import json
import re
import subprocess
import sys

from prepare_next_validation import require_guard
from check_hole_recovery_regressions_v5 import digest, identical, stage, write_new, GUARD_OK


ROOT = Path(__file__).resolve().parent
BASE = ROOT / 'scrollfiesta-comparison'
FIXTURE = BASE / 'next-zplus32-halo13-v1'
DEST = BASE / 'hole-recovery-v5/halo-regressions-v5-01'
BINARY = BASE / 'build/cube_mesh.holefill-v5'
STAGES = ('step7_cc_bpa', 'step8_holefill', 'step11_kibble', 'step12_final')


def main():
    guard = require_guard()
    assert not DEST.exists(), f'Preserve prior run: {DEST}'
    manifest_path = FIXTURE / 'frozen-input.json'
    evaluation_path = FIXTURE / 'evaluation-v2/results.json'
    summary_path = FIXTURE / 'evaluation-v2/summary.json'
    manifest = json.loads(manifest_path.read_text())
    evaluation = json.loads(evaluation_path.read_text())
    assert evaluation['passed'] and not evaluation['failures']
    assert json.loads(summary_path.read_text())['passed']
    assert digest(manifest_path) == evaluation['provenance']['frozen_input_sha256']
    assert digest(ROOT / 'prepare_next_validation.py') == manifest['preparer_sha256']
    assert digest(FIXTURE / 'run_case.py') == manifest['runner_sha256']
    assert digest(Path(manifest['source_volume'])) == manifest['source_sha256']
    prior_v5_path = BASE / 'hole-recovery-v5/regressions-v5-01/regressions.json'
    prior_v5 = json.loads(prior_v5_path.read_text())
    assert prior_v5['success'] and prior_v5['all_finals_byte_identical_to_v4_v2']
    binary_sha = digest(BINARY)
    assert binary_sha == prior_v5['binary_sha256'], 'Use v5 already checked in the three regressions'
    evidence = {str(path): digest(path) for path in
                (manifest_path, evaluation_path, summary_path, prior_v5_path,
                 ROOT / 'prepare_next_validation.py', FIXTURE / 'run_case.py',
                 ROOT / 'check_hole_recovery_regressions_v5.py')}
    plan = {}
    for side in ('left', 'right'):
        name = f'v4-{side}'
        frozen = manifest['cases'][name]
        saved = evaluation['cases'][name]
        stdin_path = FIXTURE / frozen['stdin_file']
        assert stdin_path.stat().st_size == frozen['bytes']
        assert digest(stdin_path) == frozen['stdin_sha256']
        assert digest(Path(frozen['binary'])) == frozen['binary_sha256']
        old_command = frozen['command']
        assert old_command[0] == frozen['binary'] and old_command[1] == '--stdin-raw'
        assert old_command.count('--dump-obj') == 1
        dump_index = old_command.index('--dump-obj') + 1
        assert old_command[dump_index] == frozen['output_directory']
        started_path = FIXTURE / f'{name}-started.json'
        finished_path = FIXTURE / f'{name}-finished.json'
        started = json.loads(started_path.read_text())
        assert started['command'] == old_command
        assert started['binary_sha256'] == frozen['binary_sha256']
        assert started['stdin_sha256'] == frozen['stdin_sha256']
        assert json.loads(finished_path.read_text())['returncode'] == 0
        execution = saved['execution']
        assert execution['valid'] and execution['runner_status']['returncode'] == 0
        assert execution['pipeline_statuses'] and all(s == 'OK' for s in execution['pipeline_statuses'])
        assert execution['guard_totals'] and all(n == 0 for n in execution['guard_totals'].values())
        retention = saved['source_retention_step7_to_step8']
        assert retention['retained'] and retention['missing_or_reoriented_faces'] == 0
        # Recover the literal historical environment from the observed runner log.
        log_path = Path(execution['log'])
        observed = [json.loads(line) for line in log_path.read_text().splitlines()
                    if line.startswith('{"case":')]
        assert len(observed) == 1 and observed[0]['case'] == name
        assert observed[0]['command'] == old_command
        assert Path(observed[0]['stdin']) == stdin_path
        env = dict(observed[0]['environment'])
        assert env.get('VES_HOLE_RECOVERY_SEARCH', '0') == '0', 'Historical baseline must have search OFF'
        env['VES_HOLE_RECOVERY_SEARCH'] = '1'
        command = list(old_command)
        command[0] = str(BINARY)
        command[dump_index] = str(DEST / side / 'obj')
        assert all(a == b for i, (a, b) in enumerate(zip(command, old_command))
                   if i not in (0, dump_index)), 'Only binary/output arguments may change'
        references = {}
        for stage_name in STAGES:
            previous = saved['stages'][stage_name]
            path = Path(previous['path'])
            assert path == stage(Path(frozen['output_directory']), stage_name)
            assert digest(path) == previous['sha256'], f'Changed frozen {name}/{stage_name}'
            references[stage_name] = dict(path=str(path), sha256=previous['sha256'])
            for field in ('metrics_file',):
                artifact = Path(previous[field])
                evidence[str(artifact)] = digest(artifact)
            if 'audit' in previous:
                assert previous['audit']['summary']['conflicts'] == 0
                for field in ('result_file', 'pairs_file'):
                    artifact = Path(previous['audit'][field])
                    evidence[str(artifact)] = digest(artifact)
        for path in (stdin_path, Path(frozen['binary']), started_path, finished_path, log_path):
            evidence[str(path)] = digest(path)
        plan[side] = dict(command=command, frozen_command=old_command,
                          stdin_path=str(stdin_path), stdin_sha256=frozen['stdin_sha256'],
                          environment=env, references=references,
                          source_retention_reused_from=f'{evaluation_path}#cases/{name}/source_retention_step7_to_step8')
    DEST.mkdir(parents=True)
    write_new(DEST / 'plan.json', dict(binary=str(BINARY), binary_sha256=binary_sha,
              script_sha256=digest(Path(__file__)), guard=guard, cases=plan,
              frozen_evidence_sha256=evidence,
              difference_policy='Stop; require independent exact and native audit before accepting changed geometry'))
    results = {}
    active_side = None
    try:
        for side, record in plan.items():
            active_side = side
            folder = DEST / side
            folder.mkdir()
            assert digest(BINARY) == binary_sha
            assert digest(Path(record['stdin_path'])) == record['stdin_sha256']
            write_new(folder / 'command.json', dict(record, binary_sha256=binary_sha))
            with Path(record['stdin_path']).open('rb') as stdin, (folder / 'meshing.log').open('x') as log:
                subprocess.run(record['command'], stdin=stdin, env=record['environment'],
                               stdout=log, stderr=subprocess.STDOUT, check=True)
            text = (folder / 'meshing.log').read_text()
            statuses = re.findall(r'\bStatus:\s*(\S+)', text)
            guards = [line for line in text.splitlines() if 'Guard:' in line]
            assert statuses and all(value == 'OK' for value in statuses), f'Status failure: {side}'
            assert guards and all(GUARD_OK in line for line in guards), f'Guard changed: {side}'
            checks = {}
            for stage_name, reference in record['references'].items():
                output = stage(folder / 'obj', stage_name)
                previous = Path(reference['path'])
                assert digest(previous) == reference['sha256'], 'Historical geometry changed during run'
                checks[stage_name] = dict(path=str(output), sha256=digest(output), reference=reference,
                    byte_identical_to_v4=identical(output, previous))
            outcome = dict(status_ok=True, guard_changes=0, stages=checks,
                           stdin_sha256=record['stdin_sha256'], binary_sha256=binary_sha)
            if not all(value['byte_identical_to_v4'] for value in checks.values()):
                outcome.update(success=False, state='blocked_exact_audit_required',
                    prior_audits_reused=False,
                    reason='Changed stage7/8/11/12; exact source-preservation and duplicate/intersection audit required, not native-only acceptance')
                write_new(folder / 'exact-audit-required.json', outcome)
                write_new(DEST / 'blocked.json', dict(case=side, completed_cases=results, **outcome))
                print(json.dumps(outcome), flush=True)
                return 2
            outcome.update(success=True, state='byte-identical',
                evidence_reused_from=f'{evaluation_path}#cases/v4-{side}', prior_audits_reused=True)
            write_new(folder / 'result.json', outcome)
            results[side] = outcome
            print(side, 'stages7/8/11/12 byte-identical v4; evaluation-v2 reused', flush=True)
        for filename, expected in evidence.items():
            assert digest(Path(filename)) == expected, f'Frozen evidence changed: {filename}'
    except Exception as error:
        write_new(DEST / 'failed.json', dict(case=active_side, error=str(error),
                  completed_cases=results, success=False, incomplete=True))
        raise
    write_new(DEST / 'regressions.json', dict(success=True, binary_sha256=binary_sha,
              VES_HOLE_RECOVERY_SEARCH='1', stages7_8_11_12_byte_identical_to_v4=True,
              cases=results, evaluation_reused_from=str(evaluation_path),
              union_and_seam_metrics_reused=True,
              note='Both final cores are byte-identical; no new audit, union, seam measurement or weld performed'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
