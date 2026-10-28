"""Synthetic replay/forgery controls; execute only under the project guard."""

from contextlib import redirect_stderr, redirect_stdout
import copy
import hashlib
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest

import verify_patch_coverage_witnesses as replay


T = ((0.0, 0.0, 0.0), (0.125, 0.0, 0.0), (0.0, 0.125, 0.0))
U = tuple((x, y, 0.125) for x, y, _ in T)
RETAINED = tuple((x, y, 5.0) for x, y, _ in T)


def payload(triangles):
    vertices = [p for triangle in triangles for p in triangle]
    vd = b"".join(struct.pack("<fff", *p) for p in vertices)
    fd = b"".join(struct.pack("<iii", 3*i, 3*i+1, 3*i+2) for i in range(len(triangles)))
    return struct.pack("<8sIIIIQQQQQ", b"VESMESH1", 1, 0x01020304, 0, 64,
                       len(vertices), len(triangles), 64, 0, 64+len(vd)) + vd + fd


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        metadata = {}
        for name, triangles in (("source", [RETAINED]), ("before", [RETAINED, T]), ("after", [RETAINED, U])):
            path = self.root / (name+".vmesh")
            data = payload(triangles)
            path.write_bytes(data)
            metadata[name] = {"path": str(path), "sha256": hashlib.sha256(data).hexdigest(),
                              "vertices": len(triangles)*3, "faces": len(triangles), "flags": 0}
        direction = {"certified": True, "termination": "certified", "input_source_faces": 1,
                     "unique_source_geometries": 1, "input_target_faces": 2,
                     "unique_target_geometries": 2, "visited_cells": 1, "subdivisions": 0,
                     "certified_leaf_cells": 1, "maximum_depth_seen": 0,
                     "unresolved_frontier_cells_at_stop": 0,
                     "witnesses": [[1, "", 1, replay.DENOMINATOR, 0, 0]]}
        self.certificate = {"schema": "continuous-patch-coverage-v2", "passed": True,
                            "status": "certified", "delta_exact": "1/4", "delta_squared_exact": "1/16",
                            "include_retained_background": True, **metadata,
                            "missing_or_reoriented_source_faces_before": 0,
                            "missing_or_reoriented_source_faces_after": 0,
                            "before_patch_faces": 1, "after_patch_faces": 1,
                            "before_patch_face_indices": [1], "after_patch_face_indices": [1],
                            "budget_declared_before_geometry_checks": {"max_depth": 16},
                            "proof": {"barycentric_denominator": replay.DENOMINATOR},
                            "directions": {name: copy.deepcopy(direction) for name in replay.DIRECTION_NAMES}}

    def write_certificate(self, certificate=None):
        path = self.root / "certificate.json"
        path.write_text(json.dumps(self.certificate if certificate is None else certificate))
        return path

    def verify(self, certificate=None, expected=2):
        return replay.verify_certificate(self.write_certificate(certificate), expected)

    def test_exact_replay_passes_without_producer_import(self):
        result = self.verify()
        self.assertTrue(result["passed"])
        self.assertEqual(result["witnesses_verified"], 2)
        self.assertEqual(result["hausdorff_upper_bound_exact"], "1/4")

    def test_finite_subdivision_partition_and_prefix_forgery(self):
        direction = self.certificate["directions"][replay.DIRECTION_NAMES[0]]
        direction.update(visited_cells=5, subdivisions=1, certified_leaf_cells=4, maximum_depth_seen=1,
                         witnesses=[[1, str(i), 1, replay.DENOMINATOR, 0, 0] for i in range(4)])
        self.assertTrue(self.verify(expected=5)["passed"])
        direction["witnesses"][-1][1] = "00"
        direction["maximum_depth_seen"] = 2
        with self.assertRaisesRegex(replay.ReplayFailure, "prefix"):
            self.verify(expected=5)

    def test_incomplete_partition_fails(self):
        direction = self.certificate["directions"][replay.DIRECTION_NAMES[0]]
        direction.update(certified_leaf_cells=3, witnesses=[[1, str(i), 1, replay.DENOMINATOR, 0, 0] for i in range(3)])
        with self.assertRaisesRegex(replay.ReplayFailure, "incomplete"):
            self.verify(expected=4)

    def test_invalid_weights_indices_path_and_false_bound_fail(self):
        for modification in ("negative_weight", "bad_sum", "target_index", "root_index", "path", "false_bound"):
            with self.subTest(modification=modification):
                certificate = copy.deepcopy(self.certificate)
                witness = certificate["directions"][replay.DIRECTION_NAMES[0]]["witnesses"][0]
                if modification == "negative_weight":
                    witness[3:] = [-1, replay.DENOMINATOR+1, 0]
                elif modification == "bad_sum":
                    witness[3] -= 1
                elif modification == "target_index":
                    witness[2] = 2
                elif modification == "root_index":
                    witness[0] = 0
                elif modification == "path":
                    witness[1] = "4"
                else:
                    witness[2] = 0  # Retained target is five voxels away.
                with self.assertRaises(replay.ReplayFailure):
                    self.verify(certificate)

    def test_false_identical_and_wrong_threshold_fail(self):
        for modification in ("identical", "delta"):
            certificate = copy.deepcopy(self.certificate)
            if modification == "identical":
                certificate["directions"][replay.DIRECTION_NAMES[0]]["witnesses"] = [[1, "", 1, "identical"]]
            else:
                certificate["delta_exact"] = "1/3"
            with self.assertRaises(replay.ReplayFailure):
                self.verify(certificate)

    def test_identical_witness_is_accepted_only_for_exact_geometry(self):
        path = Path(self.certificate["after"]["path"])
        data = payload([RETAINED, T])
        path.write_bytes(data)
        self.certificate["after"]["sha256"] = hashlib.sha256(data).hexdigest()
        for direction in self.certificate["directions"].values():
            direction["witnesses"] = [[1, "", 1, "identical"]]
        self.assertTrue(self.verify()["passed"])

    def test_sha_source_retention_and_expected_count_fail_closed(self):
        certificate = copy.deepcopy(self.certificate)
        certificate["before"]["sha256"] = "0"*64
        with self.assertRaisesRegex(replay.ReplayFailure, "sha256"):
            self.verify(certificate)
        path = Path(self.certificate["before"]["path"])
        data = payload([tuple(reversed(RETAINED)), T])
        path.write_bytes(data)
        self.certificate["before"]["sha256"] = hashlib.sha256(data).hexdigest()
        with self.assertRaisesRegex(replay.ReplayFailure, "source geometry"):
            self.verify()
        with self.assertRaisesRegex(replay.ReplayFailure, "3303"):
            replay.verify_certificate(self.write_certificate())

    def test_duplicate_json_keys_and_memory_budget_fail_closed(self):
        path = self.root / "duplicate.json"
        path.write_text('{"passed": true, "passed": false}')
        with self.assertRaisesRegex(replay.ReplayFailure, "duplicate JSON key"):
            replay.verify_certificate(path, 2)
        with self.assertRaisesRegex(replay.ReplayFailure, "memory"):
            replay.verify_certificate(self.write_certificate(), 2, replay.Budget(max_memory_mib=1))

    def test_cli_exclusive_output_and_failure_record(self):
        certificate = self.write_certificate()
        output = self.root / "verified.json"
        args = ["--certificate", str(certificate), "--output", str(output), "--expected-witnesses", "2"]
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(replay.main(args), 0)
            first = output.read_bytes()
            self.assertEqual(replay.main(args), 2)
            self.assertEqual(output.read_bytes(), first)
            failed = self.root / "failed.json"
            self.assertEqual(replay.main(["--certificate", str(certificate), "--output", str(failed)]), 1)
        self.assertFalse(json.loads(failed.read_text())["passed"])


if __name__ == "__main__":
    unittest.main()
