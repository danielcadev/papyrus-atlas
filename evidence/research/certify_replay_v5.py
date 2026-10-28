"""Reuse saved-mesh certificates only after exact oriented geometry equality."""
from collections import Counter
import json
from pathlib import Path
from prepare_next_validation import require_guard, sha256
from exact_patch_intersections import read_mesh, cyclic_key

require_guard()
root = Path(__file__).resolve().parent
base = root / 'scrollfiesta-comparison'
dest = base / 'hole-recovery-v5'
output = dest / 'replay-certificate.json'
assert not output.exists()
replay, report = read_mesh(dest / 'replay-on.vmesh')
saved, saved_report = read_mesh(dest / 'saved-evaluation-02/combined.vmesh')
geometry = lambda ts: Counter(cyclic_key(t.points) for t in ts)
assert geometry(replay) == geometry(saved), 'Changed geometry requires fresh audits'
assert (dest / 'replay-off.vmesh').read_bytes() == (base / 'holefill-repair-v4/replay.vmesh').read_bytes()
evidence = [dest / 'saved-evaluation-02' / n for n in ('strict.json', 'native.json', 'metrics.json')]
evidence.append(dest / 'continuous-coverage-02.json')
result = dict(passed=True, replay=report, certified_saved_geometry=saved_report,
              exact_oriented_geometry_equal=True, flag_zero_byte_identical_to_v4=True,
              evidence_reused=[dict(path=str(p), sha256=sha256(p)) for p in evidence],
              limits='Equality reuses saved geometry evidence; does not certify the full pipeline or anatomy.')
with output.open('x') as stream:
    json.dump(result, stream, indent=2)
    stream.write('\n')
print(json.dumps(dict(passed=True, output=str(output))))
