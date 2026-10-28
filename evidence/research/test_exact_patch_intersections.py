"""Independent synthetic controls. Execute only under the project guard."""

from contextlib import redirect_stderr, redirect_stdout
import io
import itertools
import json
from pathlib import Path
import struct
import tempfile
import unittest

import exact_patch_intersections as exact


A = ((0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (0.0, 2.0, 0.0))


def payload(triangles, flags=0):
    vertices = [p for t in triangles for p in t]
    vd = b"".join(struct.pack("<fff", *p) for p in vertices)
    ud = b""
    if flags & 1:
        ud = b"".join(struct.pack("<dd" if flags & 2 else "<ff", 0.0, 0.0)
                      for _ in vertices)
    fd = b"".join(struct.pack("<iii", 3*i, 3*i+1, 3*i+2) for i in range(len(triangles)))
    return struct.pack("<8sIIIIQQQQQ", b"VESMESH1", 1, 0x01020304, flags, 64,
                       len(vertices), len(triangles), 64,
                       64+len(vd) if flags & 1 else 0, 64+len(vd)+len(ud)) + vd + ud + fd


class ExactIntersectionTests(unittest.TestCase):
    def check(self, b, allowed, dimension=None, a=A):
        result = exact.pair_check(exact.Triangle(tuple(a)), exact.Triangle(tuple(b)))
        self.assertEqual(result["allowed"], allowed, result)
        if dimension is not None:
            self.assertEqual(result["intersection_dimension"], dimension, result)
        return result

    def test_duplicate_and_reverse_duplicate(self):
        for order in itertools.permutations(A):
            result = self.check(order, False, 2)
            self.assertEqual(result["reason"], "duplicate_geometry")

    def test_point_touch_shared_corner_allowed_coplanar_and_spatial(self):
        self.check(((0, 0, 0), (-1, 0, 0), (0, -1, 0)), True, 0)
        self.check(((0, 0, 0), (-1, 0, 1), (0, -1, 1)), True, 0)

    def test_shared_edge_allowed_coplanar_and_spatial(self):
        self.check(((0, 0, 0), (2, 0, 0), (0, -1, 0)), True, 1)
        self.check(((0, 0, 0), (2, 0, 0), (0, 0, 1)), True, 1)

    def test_coplanar_overlap_beyond_shared_edge_rejected(self):
        self.check(((0, 0, 0), (2, 0, 0), (1, 1, 0)), False, 2)

    def test_coplanar_containment_and_crossing_without_shared_corners(self):
        self.check(((0.25, 0.25, 0), (0.5, 0.25, 0), (0.25, 0.5, 0)), False, 2)
        self.check(((0.5, -1, 0), (0.5, 2, 0), (1, 0.5, 0)), False, 2)

    def test_proper_stab_sharing_vertex_is_rejected_native_blind_spot(self):
        b = ((0, 0, 0), (1, 0.5, 1), (1, 0.5, -1))
        for order_a in itertools.permutations(A):
            for order_b in itertools.permutations(b):
                self.check(order_b, False, 1, order_a)
                self.check(order_a, False, 1, order_b)

    def test_spatial_crossing_without_common_corner(self):
        self.check(((0.5, 0.5, -1), (0.5, 0.5, 1), (1.5, 0.5, 0)), False, 1)

    def test_separated_parallel_and_coplanar(self):
        self.check(tuple((x, y, 0.125) for x, y, _ in A), True, -1)
        self.check(((3, 0, 0), (4, 0, 0), (3, 1, 0)), True, -1)

    def test_unindexed_boundary_touch_is_conservatively_rejected(self):
        self.check(((1, 0, 0), (1, -1, 0), (0.5, -1, 0)), False, 0)

    def test_degenerate_unsupported_and_binary32_subnormal_nondegenerate(self):
        bad = exact.Triangle(((0, 0, 0), (1, 0, 0), (2, 0, 0)))
        self.assertTrue(bad.degenerate)
        with self.assertRaises(ValueError):
            exact.pair_check(exact.Triangle(A), bad)
        tiny = struct.unpack("<f", struct.pack("<I", 1))[0]
        triangle = exact.Triangle(((0.0, 0.0, 0.0), (tiny, 0.0, 0.0), (0.0, tiny, 0.0)))
        self.assertFalse(triangle.degenerate)
        self.assertFalse(exact.pair_check(triangle, triangle)["allowed"])


class PatchCertificateTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def write(self, name, triangles, flags=0):
        path = self.root / name
        path.write_bytes(payload(triangles, flags))
        return path

    def certificate(self, source, candidate):
        return exact.make_certificate(self.write("source.vmesh", source),
                                      self.write("candidate.vmesh", candidate))

    def test_valid_patch_and_both_uv_encodings(self):
        neighbor = ((0, 0, 0), (2, 0, 0), (0, -1, 0))
        for flags in (0, 1, 3):
            source = self.write("source.vmesh", [A], flags)
            candidate = self.write("candidate.vmesh", [A[1:]+A[:1], neighbor], flags)
            report = exact.make_certificate(source, candidate)
            self.assertTrue(report["passed"], report)
            self.assertEqual(report["added_faces"], 1)
            self.assertEqual(report["exact_pairs_checked"], 1)

    def test_source_orientation_and_multiplicity_must_survive(self):
        for source, candidate in (([A], [tuple(reversed(A))]), ([A, A], [A])):
            report = self.certificate(source, candidate)
            self.assertFalse(report["passed"])
            self.assertEqual(report["missing_or_reoriented_source_faces"], 1)

    def test_added_source_and_added_added_conflicts(self):
        report = self.certificate([A], [A, A])
        self.assertFalse(report["passed"])
        self.assertEqual(report["conflicts"], 1)
        self.assertEqual(report["conflict_examples"][0]["pair_kind"], "added/source")
        remote = tuple((x+5, y, z) for x, y, z in A)
        report = self.certificate([A], [A, remote, tuple(reversed(remote))])
        self.assertFalse(report["passed"])
        self.assertEqual(report["conflicts"], 1)
        self.assertEqual(report["conflict_examples"][0]["pair_kind"], "added/added")

    def test_added_degenerate_fails_even_when_aabb_is_remote(self):
        degenerate = ((5, 0, 0), (6, 0, 0), (7, 0, 0))
        report = self.certificate([A], [A, degenerate])
        self.assertFalse(report["passed"])
        self.assertEqual(report["added_degenerate_face_indices"], [1])

    def test_invalid_layout_and_nonfinite_coordinate_are_refused(self):
        path = self.write("invalid.vmesh", [A])
        valid = path.read_bytes()
        bad_finite = bytearray(valid)
        struct.pack_into("<f", bad_finite, 64, float("inf"))
        for data in (valid[:-1], valid+b"x", bad_finite):
            path.write_bytes(data)
            with self.assertRaises(exact.MeshFormatError):
                exact.read_mesh(path)

    def test_cli_writes_exclusive_output_and_exit_status(self):
        source = self.write("source.vmesh", [A])
        candidate = self.write("candidate.vmesh", [A, A])
        output = self.root / "certificate.json"
        arguments = ["--source", str(source), "--candidate", str(candidate), "--output", str(output)]
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(exact.main(arguments), 1)
            initial = output.read_bytes()
            self.assertFalse(json.loads(initial)["passed"])
            self.assertEqual(exact.main(arguments), 2)
        self.assertEqual(output.read_bytes(), initial)


if __name__ == "__main__":
    unittest.main()
