"""Verify the reviewer's exact separating-plane witness for face selection."""
from pathlib import Path
import json
from ink_guard import require_guard
from ink_io import digest
guard=require_guard();assert guard['memory_max']<=384*1024**2
root=Path(__file__).resolve().parent
source=root/'paris4-structural-face-selection-v1/old-only-selection-frozen.json'
rows=json.loads(source.read_text())['selected'];normal=(1,-1,1)
values=[sum(a*b for a,b in zip(normal,r['native_zyx'])) for r in rows]
corner=[143,144,143];required=sum(a*b for a,b in zip(normal,corner))
assert len(rows)==12 and max(values)==133 and required==142 and required>max(values)
result=dict(guard=guard,passed=True,selected_centers=len(rows),selection_sha256=digest(source),
    separating_plane_normal_native_zyx=list(normal),maximum_over_selected_centers=max(values),
    required_ROI_corner=corner,required_corner_value=required,
    full_selected_hull_can_contain_required_ROI=False,
    conclusion='Face-v3 cannot pass its full-ROI hull prerequisite even if every selected point matches. This is a design limitation, not proof of physical deformation or registration impossibility.')
out=root/'paris4-structural-audit-v1/face-hull-design-review.json';assert not out.exists()
out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
