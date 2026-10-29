"""Offline integrity, saved-decision and exact hull-witness replay only."""
from pathlib import Path
import hashlib
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from release_guard import require_guard

def main():
    guard = require_guard()
    assert len(sys.argv) == 2
    output = Path(sys.argv[1])
    output.mkdir(exist_ok=False)
    base = Path(__file__).resolve().parent
    provenance = json.loads((base / 'EXPORT_PROVENANCE.json').read_text())
    for row in provenance['exported']:
        with (base / row['path']).open('rb') as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == row['sha256']
    evidence = base / 'evidence'
    decisions = []
    for name, count in (('paris4-structural-direct-v2', 16), ('paris4-structural-face-direct-v3', 12)):
        result = json.loads((evidence / name / 'result.json').read_text())
        assert result['selected_candidates'] == count and result['reliable_points'] == 0
        assert result['model'] is None and not result['registration_accepted']
        assert not result['ink_used'] and result['letters_verified'] == 0
        decisions.append(dict(case=name, selected=count, reliable=0))
    hull = json.loads((evidence / 'paris4-structural-audit-v1/face-hull-design-review.json').read_text())
    selection = json.loads((evidence / 'paris4-structural-face-direct-v3/old-only-selection-frozen.json').read_text())
    points = [p['native_zyx'] for p in selection['selected']]
    normal = hull['separating_plane_normal_native_zyx']
    dot = lambda p: sum(x * y for x, y in zip(p, normal))
    maximum = max(map(dot, points))
    corner_value = dot(hull['required_ROI_corner'])
    assert len(points) == 12 and maximum == hull['maximum_over_selected_centers'] == 133
    assert corner_value == hull['required_corner_value'] == 142 and maximum < corner_value
    assert not hull['full_selected_hull_can_contain_required_ROI']
    result = dict(guard=guard, passed=True, exported_hashes_verified=len(provenance['exported']),
                  saved_decisions=decisions, exact_selected_hull_exclusion_replayed=True,
                  registration_accepted=False, letters_verified=0,
                  scope='Integrity, saved trial decisions and exact plane witness; no CT sampling, fitting, anatomy or ink reproduction.')
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)

if __name__ == '__main__':
    main()
