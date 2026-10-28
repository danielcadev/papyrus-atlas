"""Run standalone controls and a real mesh replay under the resource guard."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parent))
from release_guard import require_guard

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from vesuvius_surface import Mesh, boundary_graft, recover_cycle
from vesuvius_surface.exact import Triangle, boxes_overlap, pair_check, cyclic_key

guard = require_guard()
out = Path(sys.argv[1]).resolve()
out.mkdir(exist_ok=False)
suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
with (out / "controls.log").open("x") as log:
    run = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
assert run.wasSuccessful(), (out / "controls.log").read_text()
fixtures = ROOT / "tests/fixtures"
provenance = json.loads((ROOT / "PROVENANCE.json").read_text())
for name, expected in provenance["fixture_hashes"].items():
    assert hashlib.sha256((fixtures / name).read_bytes()).hexdigest() == expected
mesh = Mesh.read(fixtures / "paris4-source.json")
cycle = json.loads((fixtures / "paris4-cycle.json").read_text())
candidate, report = recover_cycle(mesh, cycle)
(out / "recovery.json").write_text(json.dumps(report, indent=2) + "\n")
assert report["accepted"] and report["added_faces"] == 17, report
assert candidate.vertices == mesh.vertices and candidate.faces[:len(mesh.faces)] == mesh.faces
candidate.write(out / "paris4-recovered.json")
source = [Triangle(tuple(mesh.vertices[v] for v in f)) for f in mesh.faces]
added = [Triangle(tuple(candidate.vertices[v] for v in f)) for f in candidate.faces[len(mesh.faces):]]
pairs = 0
for i, tri in enumerate(added):
    assert not tri.degenerate
    for other in source + added[:i]:
        if boxes_overlap(tri.box, other.box):
            pairs += 1
            assert pair_check(tri, other)["allowed"]
reference = Mesh.read(fixtures / "paris4-reference.json")
def oriented(mesh):
    return Counter(cyclic_key(tuple(mesh.vertices[v] for v in f)) for f in mesh.faces)
graft = json.loads((fixtures / "graft-input.json").read_text())
expected = json.loads((fixtures / "graft-expected.json").read_text())
actual = boundary_graft(graft["labels"], graft["adjacency"], graft["conflicts"], complete=graft["complete"])
assert actual["labels"] == expected["labels"]
result = {"passed": True, "guard": guard, "unit_controls": run.testsRun,
          "graft_recovered": actual["recovered"], "graft_labels_match_export": True,
          "source_faces": len(mesh.faces), "final_faces": len(candidate.faces),
          "added_faces": report["added_faces"], "source_vertices_and_indexed_faces_unchanged": True,
          "final_exact_pairs": pairs, "final_exact_forbidden_contacts": 0,
          "same_oriented_geometry_as_historical_v5": oriented(candidate) == oriented(reference),
          "runtime": "Python standard library only; no ScrollFiesta, native binary, NumPy, model, network or GPU required.",
          "scope": "Exported graft-graph replay and independent mesh-stage hole recovery. Not independent CT extraction, segmentation, flattening, anatomy or text."}
(out / "verification.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2), flush=True)
