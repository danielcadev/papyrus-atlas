"""Synthetic controls for the continuous certificate; run under project guard."""

from contextlib import redirect_stderr, redirect_stdout
from fractions import Fraction
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest

import certify_patch_coverage as coverage
from exact_patch_intersections import Triangle


TRIANGLE = ((0.0, 0.0, 0.0), (0.25, 0.0, 0.0), (0.0, 0.25, 0.0))
DELTA = Fraction(1, 4)
BUDGET = coverage.Budget(max_cells=5000, max_depth=8, max_witnesses=5000)


def shifted(triangle, z):
    return tuple((x, y, old_z+z) for x, y, old_z in triangle)


def payload(triangles):
    vertices = [p for triangle in triangles for p in triangle]
    vd = b"".join(struct.pack("<fff", *p) for p in vertices)
    fd = b"".join(struct.pack("<iii", 3*i, 3*i+1, 3*i+2) for i in range(len(triangles)))
    return struct.pack("<8sIIIIQQQQQ", b"VESMESH1", 1, 0x01020304, 0, 64,
                       len(vertices), len(triangles), 64, 0, 64+len(vd)) + vd + fd


class CoverageMathTests(unittest.TestCase):
    def direction(self, a, b, budget=BUDGET):
        return coverage.certify_direction([Triangle(a, 0)], [Triangle(b, 1)], DELTA, budget)

    def test_ball_squared_test_accepts_equality_and_rejects_wrong_sign(self):
        self.assertTrue(coverage.ball_covers(Fraction(1, 64), Fraction(1, 64), Fraction(1, 16)))
        self.assertTrue(coverage.ball_covers(Fraction(1, 16), Fraction(0), Fraction(1, 16)))
        self.assertFalse(coverage.ball_covers(Fraction(1), Fraction(0), Fraction(1, 16)))
        self.assertFalse(coverage.ball_covers(Fraction(1, 16)+Fraction(1, 1 << 100), Fraction(0), Fraction(1, 16)))

    def test_identical_large_triangle_has_exact_zero_distance_witness(self):
        large = ((0, 0, 0), (8, 0, 0), (0, 8, 0))
        result = self.direction(large, tuple(reversed(large)))
        self.assertTrue(result["certified"], result)
        self.assertEqual(result["visited_cells"], 1)
        self.assertEqual(result["witnesses"], [[0, "", 1, "identical"]])

    def test_parallel_triangles_inside_delta_certify_both_directions(self):
        other = shifted(TRIANGLE, 0.125)
        for a, b in ((TRIANGLE, other), (other, TRIANGLE)):
            result = self.direction(a, b)
            self.assertTrue(result["certified"], result)
            self.assertGreater(result["subdivisions"], 0)

    def test_exported_witnesses_cover_root_and_reconstruct_exact_bound(self):
        other = shifted(TRIANGLE, 0.125)
        result = self.direction(TRIANGLE, other)
        paths = [w[1] for w in result["witnesses"]]
        self.assertEqual(sum(Fraction(1, 4**len(path)) for path in paths), 1)
        self.assertFalse(any(a != b and b.startswith(a) for a in paths for b in paths))
        target = Triangle(other).exact
        for root, path, target_index, *weights in result["witnesses"]:
            self.assertEqual((root, target_index), (0, 1))
            cell = Triangle(TRIANGLE).exact
            for digit in path:
                cell = coverage.subdivide(cell)[int(digit)]
            center = tuple(sum(p[d] for p in cell)/3 for d in range(3))
            r2 = max(sum((p[d]-center[d])**2 for d in range(3)) for p in cell)
            self.assertEqual(sum(weights), coverage.BARYCENTRIC_DENOMINATOR)
            self.assertTrue(all(w >= 0 for w in weights))
            q = tuple(sum(weights[i]*target[i][d] for i in range(3)) /
                      coverage.BARYCENTRIC_DENOMINATOR for d in range(3))
            d2 = sum((center[d]-q[d])**2 for d in range(3))
            t = DELTA*DELTA-d2-r2
            self.assertGreaterEqual(t, 0)
            self.assertGreaterEqual(t*t, 4*d2*r2)

    def test_separation_above_delta_cannot_pass(self):
        result = self.direction(TRIANGLE, shifted(TRIANGLE, 0.5),
                                coverage.Budget(max_cells=40, max_depth=4))
        self.assertFalse(result["certified"])
        self.assertTrue(result["termination"].startswith("inconclusive_"))

    def test_exact_delta_parallel_positive_area_is_conservatively_inconclusive(self):
        result = self.direction(TRIANGLE, shifted(TRIANGLE, 0.25),
                                coverage.Budget(max_cells=40, max_depth=4))
        self.assertFalse(result["certified"])
        self.assertEqual(result["termination"], "inconclusive_depth_limit")

    def test_exact_delta_degenerate_point_is_certified(self):
        a = ((0.0, 0.0, 0.0),) * 3
        b = ((0.0, 0.0, 0.25),) * 3
        self.assertTrue(self.direction(a, b)["certified"])

    def test_rational_weights_remain_inside_target(self):
        for weights in ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0),
                        (1/3, 1/3, 1/3), (0.9, 0.9, -0.8)):
            integers = coverage.rational_weights(weights)
            self.assertTrue(all(w >= 0 for w in integers))
            self.assertEqual(sum(integers), coverage.BARYCENTRIC_DENOMINATOR)

    def test_midpoint_subdivision_has_exact_rational_coordinates(self):
        triangle = Triangle(TRIANGLE).exact
        children = coverage.subdivide(triangle)
        self.assertEqual(len(children), 4)
        self.assertEqual(children[0][0], triangle[0])
        self.assertEqual(children[0][1], (Fraction(1, 8), Fraction(0), Fraction(0)))
        self.assertEqual(children[3][2], children[0][2])

    def test_budget_failures_are_inconclusive(self):
        other = shifted(TRIANGLE, 0.125)
        cases = ((coverage.Budget(max_cells=1), "inconclusive_cell_limit"),
                 (coverage.Budget(max_depth=0), "inconclusive_depth_limit"),
                 (coverage.Budget(max_pending_cells=1), "inconclusive_pending_cell_limit"),
                 (coverage.Budget(max_memory_mib=1), "inconclusive_memory_limit"))
        for budget, termination in cases:
            with self.subTest(termination=termination):
                result = self.direction(TRIANGLE, other, budget)
                self.assertFalse(result["certified"])
                self.assertEqual(result["termination"], termination)

    def test_unoriented_geometric_duplicate_is_proved_once(self):
        triangles = [Triangle(TRIANGLE, 0), Triangle(tuple(reversed(TRIANGLE)), 1)]
        result = coverage.certify_direction(triangles, [Triangle(TRIANGLE, 2)], DELTA, BUDGET)
        self.assertTrue(result["certified"])
        self.assertEqual(result["input_source_faces"], 2)
        self.assertEqual(result["unique_source_geometries"], 1)
        self.assertEqual(result["visited_cells"], 1)

    def test_exact_aabb_filter_includes_boundary_and_rejects_one_float32_ulp_above(self):
        origin = ((0.0, 0.0),) * 3
        at_delta = ((0.0, 0.0), (0.0, 0.0), (0.25, 0.25))
        next_value = struct.unpack("<f", struct.pack("<I", 0x3e800001))[0]
        above_delta = ((0.0, 0.0), (0.0, 0.0), (next_value, next_value))
        self.assertTrue(coverage.boxes_within_delta(origin, at_delta, DELTA*DELTA))
        self.assertFalse(coverage.boxes_within_delta(origin, above_delta, DELTA*DELTA))


class CoverageFileTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def write(self, name, triangles):
        path = self.root / name
        path.write_bytes(payload(triangles))
        return path

    def inputs(self):
        retained = shifted(TRIANGLE, 5.0)
        source = self.write("source.vmesh", [retained])
        before = self.write("before.vmesh", [retained, TRIANGLE, tuple(reversed(TRIANGLE))])
        after = self.write("after.vmesh", [retained, shifted(TRIANGLE, 0.125)])
        return before, source, after

    def test_oriented_multiset_subtraction_and_bidirectional_full_patch_proof(self):
        before, source, after = self.inputs()
        report = coverage.make_certificate(before, source, after, DELTA, BUDGET)
        self.assertTrue(report["passed"], report)
        self.assertEqual(report["before_patch_faces"], 2)
        self.assertEqual(report["after_patch_faces"], 1)
        old = report["directions"]["before_patch_to_after_patch"]
        self.assertEqual(old["input_source_faces"], 2)
        self.assertEqual(old["unique_source_geometries"], 1)
        self.assertEqual(report["delta_exact"], "1/4")

    def test_missing_or_reoriented_source_fails_before_coverage(self):
        before, source, after = self.inputs()
        retained = shifted(TRIANGLE, 5.0)
        after.write_bytes(payload([tuple(reversed(retained)), shifted(TRIANGLE, 0.125)]))
        report = coverage.make_certificate(before, source, after, DELTA, BUDGET)
        self.assertFalse(report["passed"])
        self.assertEqual(report["status"], "invalid_source_retention")
        self.assertIsNone(report["directions"])
        self.assertEqual(report["missing_or_reoriented_source_faces_after"], 1)

    def test_full_surface_coverage_can_use_shared_background(self):
        retained = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
        remote = tuple((x+100, y, z) for x, y, z in retained)
        source = self.write("background.vmesh", [retained, remote])
        before = self.write("background_before.vmesh", [retained, remote, shifted(TRIANGLE, 0.1875)])
        after = self.write("background_after.vmesh", [retained, remote, shifted(TRIANGLE, -0.1875)])
        limited = coverage.Budget(max_cells=40, max_depth=4)
        patch_only = coverage.make_certificate(before, source, after, DELTA, limited)
        self.assertFalse(patch_only["passed"])
        full = coverage.make_certificate(before, source, after, DELTA, BUDGET,
                                         include_retained_background=True)
        self.assertTrue(full["passed"], full)
        self.assertIsNotNone(full["retained_background_coverage"])
        for direction in full["directions"].values():
            self.assertTrue(direction["exact_target_aabb_filter_enabled"])
            self.assertEqual(direction["unique_target_geometries"], 3)
            self.assertEqual(direction["target_aabb_filter_by_root"][0]["target_geometries_after_filter"], 1)
            self.assertTrue(all(witness[2] == 0 for witness in direction["witnesses"]))

    def test_cli_refuses_overwrite(self):
        before, source, after = self.inputs()
        output = self.root / "proof.json"
        arguments = ["--before", str(before), "--source", str(source), "--after", str(after),
                     "--output", str(output), "--max-cells", "5000", "--max-depth", "8"]
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(coverage.main(arguments), 0)
            first = output.read_bytes()
            self.assertTrue(json.loads(first)["passed"])
            self.assertEqual(coverage.main(arguments), 2)
        self.assertEqual(output.read_bytes(), first)


if __name__ == "__main__":
    unittest.main()
