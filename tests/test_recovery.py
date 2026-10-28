"""Meaningful independent controls for admission, contacts and preservation."""
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from vesuvius_surface import Mesh, boundary_graft, recover_cycle
from vesuvius_surface.exact import Triangle, pair_check


class GraftControls(unittest.TestCase):
    def test_alternative_owner_current_conflicts_and_retry(self):
        labels = [i//16 for i in range(32)] + list(range(2, 7))
        old = list(labels)
        adjacency = [(32,0),(32,16),(33,0),(34,32),(35,34),(36,33)]
        conflicts = [(32,0),(33,0),(35,32)]
        refusal = boundary_graft(labels, adjacency, conflicts, complete=False)
        self.assertFalse(refusal["accepted"])
        self.assertEqual(refusal["labels"], labels)
        result = boundary_graft(labels, adjacency, conflicts, complete=True)
        self.assertEqual(result["recovered"], 2)
        self.assertEqual(result["labels"][32:37], [1,3,1,5,6])
        self.assertEqual(labels, old)
        retry = boundary_graft(labels, [(32,0),(33,16),(32,33)], [(32,0)], complete=True)
        self.assertEqual(retry["labels"][32:34], [1,1])

    def test_invalid_conflict_and_budget_fail_closed(self):
        labels = [0] * 16 + [1]
        for adjacency, conflicts in [([(17,0)],[]), ([(16,0)],[(0,1)]), ([(16,16)],[])]:
            result = boundary_graft(labels, adjacency, conflicts, complete=True)
            self.assertFalse(result["accepted"])
            self.assertEqual(result["labels"], labels)

    def test_live_exported_real_graph(self):
        folder = Path(__file__).parent / "fixtures"
        data = json.loads((folder / "graft-input.json").read_text())
        expected = json.loads((folder / "graft-expected.json").read_text())
        result = boundary_graft(data["labels"], data["adjacency"], data["conflicts"], complete=data["complete"])
        self.assertTrue(result["accepted"])
        self.assertEqual(result["labels"], expected["labels"])
        self.assertEqual(result["recovered"], 27)


class GeometryControls(unittest.TestCase):
    def test_cli_graft_executes_without_site_packages(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "graft.json"
            command = [sys.executable, "-I", "-S", str(root / "tools/run_cli.py"), "graft", str(root / "tests/fixtures/graft-input.json"), str(output)]
            run = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(output.read_text())["recovered"], 27)
            saved = output.read_bytes()
            again = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(again.returncode, 0)
            self.assertEqual(output.read_bytes(), saved)

    def test_exact_shared_vertex_blind_spot_and_duplicate(self):
        a = Triangle(((0.,0.,0.), (2.,0.,0.), (0.,2.,0.)))
        crossing = Triangle(((0.,0.,0.), (1.,1.,-1.), (1.,1.,1.)))
        self.assertFalse(pair_check(a, crossing)["allowed"])
        duplicate = Triangle(tuple(reversed(a.points)))
        self.assertFalse(pair_check(a, duplicate)["allowed"])
        neighbor = Triangle(((2.,0.,0.), (0.,0.,0.), (0.,-2.,0.)))
        self.assertTrue(pair_check(a, neighbor)["allowed"])

    def test_square_hole_and_atomic_budget_refusal(self):
        # Flat square annulus, outward triangle orientation consistent.
        mesh = Mesh(((-1.,-1.,0.), (1.,-1.,0.), (1.,1.,0.), (-1.,1.,0.),
                     (-2.,-2.,0.), (2.,-2.,0.), (2.,2.,0.), (-2.,2.,0.)),
                    ((4,5,1),(4,1,0),(5,6,2),(5,2,1),(6,7,3),(6,3,2),(7,4,0),(7,0,3)))
        candidate, report = recover_cycle(mesh, [0,1,2,3])
        self.assertTrue(report["accepted"], report)
        self.assertEqual(report["added_faces"], 2)
        self.assertEqual(candidate.vertices, mesh.vertices)
        self.assertEqual(candidate.faces[:len(mesh.faces)], mesh.faces)
        for kwargs in ({"node_budget":0}, {"pair_budget":0}, {"node_budget":2000001}):
            rejected, reason = recover_cycle(mesh, [0,1,2,3], **kwargs)
            self.assertFalse(reason["accepted"])
            self.assertIs(rejected, mesh)
        invalid, reason = recover_cycle(mesh, [0,1,1,3])
        self.assertIs(invalid, mesh)
        self.assertFalse(reason["accepted"])

    def test_json_obj_roundtrip_and_overwrite_refusal(self):
        mesh = Mesh(((0.,0.,0.), (1.,0.,0.), (0.,1.,0.)), ((0,1,2),))
        with tempfile.TemporaryDirectory() as folder:
            for extension in ("json", "obj"):
                path = Path(folder) / ("mesh." + extension)
                mesh.write(path)
                self.assertEqual(Mesh.read(path), mesh)
                with self.assertRaises(FileExistsError):
                    mesh.write(path)

    def test_hole_with_crossing_obstacle_is_refused(self):
        vertices = ((-1.,-1.,0.), (1.,-1.,0.), (1.,1.,0.), (-1.,1.,0.),
                    (-2.,-2.,0.), (2.,-2.,0.), (2.,2.,0.), (-2.,2.,0.),
                    (0.,0.,-1.), (0.,0.5,1.), (0.5,0.,1.))
        faces = ((4,5,1),(4,1,0),(5,6,2),(5,2,1),(6,7,3),(6,3,2),(7,4,0),(7,0,3),(8,9,10))
        mesh = Mesh(vertices, faces)
        candidate, report = recover_cycle(mesh, [0,1,2,3])
        self.assertIs(candidate, mesh)
        self.assertFalse(report["accepted"])
        self.assertEqual(report["added_faces"], 0)


if __name__ == "__main__":
    unittest.main()
