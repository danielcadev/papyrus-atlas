"""Synthetic controls for the independent VMESH certificate (stdlib only).

Run under the project's systemd/resource guard:
    python3 -m unittest discover -s research -p test_exact_mesh_certificate.py -v
"""

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest

import exact_mesh_certificate as certificate


TRIANGLE = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]


def payload(vertices=TRIANGLE, faces=((0, 1, 2),), flags=0, uv=None):
    """Encode fixture bytes independently of the production reader constants."""
    vertex_data = b"".join(struct.pack("<fff", *vertex) for vertex in vertices)
    uv_data = b""
    if flags & 1:
        uv = uv if uv is not None else [(0.0, 0.0)] * len(vertices)
        uv_data = b"".join(struct.pack("<dd" if flags & 2 else "<ff", *pair) for pair in uv)
    header = struct.pack("<8sIIIIQQQQQ", b"VESMESH1", 1, 0x01020304, flags, 64,
                         len(vertices), len(faces), 64,
                         64 + len(vertex_data) if flags & 1 else 0,
                         64 + len(vertex_data) + len(uv_data))
    return header + vertex_data + uv_data + b"".join(struct.pack("<iii", *face) for face in faces)


class ExactMeshCertificateTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def write(self, data=None, name="mesh.vmesh"):
        path = self.root / name
        path.write_bytes(payload() if data is None else data)
        return path

    def inspect(self, data):
        return certificate.inspect_mesh(self.write(data))

    def test_valid_geometry_and_both_uv_encodings(self):
        for flags in (0, 1, 3):
            with self.subTest(flags=flags):
                data = payload(flags=flags)
                facts = self.inspect(data)
                self.assertEqual(facts.report["flags"], flags)
                self.assertEqual(facts.report["sha256"], hashlib.sha256(data).hexdigest())
                self.assertEqual(facts.report["exact_duplicate_groups"], 0)
                self.assertEqual(facts.report["degenerate_faces"], 0)

    def test_truncated_header_vertex_uv_face_and_trailing_bytes(self):
        data = payload(flags=3)
        for malformed in (b"", data[:63], data[:70], data[:110], data[:-1], data + b"x"):
            with self.subTest(length=len(malformed)):
                with self.assertRaises(certificate.MeshFormatError):
                    self.inspect(malformed)

    def test_header_fields_and_layout_are_strict(self):
        original = payload()
        # Explicit wire offsets, independent of the reader's header struct.
        mutations = [(0, "8s", b"NOTMESH!"), (8, "I", 2),
                     (12, "I", 0x04030201), (16, "I", 4), (16, "I", 2),
                     (20, "I", 60), (24, "Q", 0), (24, "Q", 1 << 31),
                     (32, "Q", 0), (32, "Q", (1 << 64) - 1),
                     (40, "Q", 65), (48, "Q", 100), (56, "Q", 101)]
        for offset, fmt, value in mutations:
            with self.subTest(offset=offset, value=value):
                malformed = bytearray(original)
                struct.pack_into("<" + fmt, malformed, offset, value)
                with self.assertRaises(certificate.MeshFormatError):
                    self.inspect(malformed)

    def test_uv_offsets_are_strict(self):
        for offset in (48, 56):
            with self.subTest(offset=offset):
                malformed = bytearray(payload(flags=1))
                struct.pack_into("<Q", malformed, offset, 0)
                with self.assertRaises(certificate.MeshFormatError):
                    self.inspect(malformed)

    def test_negative_and_out_of_range_indices(self):
        for index in (-1, 3, (1 << 31) - 1):
            with self.subTest(index=index):
                with self.assertRaises(certificate.MeshFormatError):
                    self.inspect(payload(faces=[(0, 1, index)]))

    def test_nonfinite_vertices_including_unreferenced_vertex(self):
        for value in (float("nan"), float("inf"), -float("inf")):
            with self.subTest(value=value):
                with self.assertRaises(certificate.MeshFormatError):
                    self.inspect(payload(vertices=TRIANGLE + [(value, 0.0, 0.0)]))

    def test_nonfinite_uvs_in_both_encodings(self):
        for flags in (1, 3):
            for value in (float("nan"), float("inf")):
                with self.subTest(flags=flags, value=value):
                    with self.assertRaises(certificate.MeshFormatError):
                        self.inspect(payload(flags=flags, uv=[(0.0, 0.0), (value, 0.0), (0.0, 0.0)]))

    def test_duplicate_ignores_ids_and_winding_and_counts_multiplicity(self):
        facts = self.inspect(payload(vertices=TRIANGLE * 2,
                                     faces=[(0, 1, 2), (5, 4, 3), (1, 2, 0)]))
        self.assertEqual(facts.report["exact_duplicate_groups"], 1)
        self.assertEqual(facts.report["nondegenerate_duplicate_groups"], 1)
        self.assertEqual(facts.report["duplicate_extra_faces"], 2)
        self.assertEqual(facts.report["duplicate_groups"][0]["face_indices"], [0, 1, 2])

    def test_one_float32_ulp_separation_is_not_welded(self):
        next_float = struct.unpack("<f", struct.pack("<I", 0x3f800001))[0]
        vertices = TRIANGLE + [(next_float, 0.0, 0.0)]
        facts = self.inspect(payload(vertices=vertices, faces=[(0, 1, 2), (0, 3, 2)]))
        self.assertEqual(facts.report["exact_duplicate_groups"], 0)

    def test_signed_zeros_are_same_geometric_coordinate(self):
        facts = self.inspect(payload(vertices=TRIANGLE + [(-0.0, -0.0, -0.0)],
                                     faces=[(0, 1, 2), (3, 2, 1)]))
        self.assertEqual(facts.report["nondegenerate_duplicate_groups"], 1)

    def test_degenerate_groups_are_separate_from_nondegenerate_groups(self):
        vertices = TRIANGLE + [(2.0, 0.0, 0.0)]
        faces = [(0, 1, 2), (2, 1, 0), (0, 1, 3), (3, 1, 0), (0, 0, 1)]
        report = self.inspect(payload(vertices=vertices, faces=faces)).report
        self.assertEqual(report["exact_duplicate_groups"], 2)
        self.assertEqual(report["nondegenerate_duplicate_groups"], 1)
        self.assertEqual(report["degenerate_duplicate_groups"], 1)
        self.assertEqual(report["degenerate_faces"], 3)

    def test_exact_degeneracy_at_binary32_extremes(self):
        tiny = struct.unpack("<f", struct.pack("<I", 1))[0]
        huge = struct.unpack("<f", struct.pack("<I", 0x7f7fffff))[0]
        for scale in (tiny, huge):
            with self.subTest(scale=scale):
                vertices = [(0.0, 0.0, 0.0), (scale, 0.0, 0.0), (0.0, scale, 0.0)]
                self.assertEqual(self.inspect(payload(vertices=vertices)).report["degenerate_faces"], 0)
                vertices[2] = (-scale, 0.0, 0.0)
                self.assertEqual(self.inspect(payload(vertices=vertices)).report["degenerate_faces"], 1)

    def test_source_cyclic_orientation_retained_but_reverse_rejected(self):
        source = self.inspect(payload())
        rotated = self.inspect(payload(vertices=TRIANGLE * 2, faces=[(4, 5, 3)]))
        reversed_face = self.inspect(payload(faces=[(0, 2, 1)]))
        self.assertTrue(certificate.source_retention(source, rotated)["retained"])
        missing = certificate.source_retention(source, reversed_face)
        self.assertFalse(missing["retained"])
        self.assertEqual(missing["missing_or_reoriented_faces"], 1)

    def test_source_multiplicity_is_not_a_set(self):
        source = self.inspect(payload(faces=[(0, 1, 2), (1, 2, 0)]))
        target = self.inspect(payload())
        missing = certificate.source_retention(source, target)
        self.assertEqual(missing["missing_or_reoriented_faces"], 1)
        self.assertEqual(missing["missing"][0]["multiplicity"], 1)
        self.assertTrue(certificate.source_retention(source, source)["retained"])

    def invoke(self, *arguments):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            return certificate.main(list(map(str, arguments)))

    def test_cli_repair_success_and_refusal_to_overwrite(self):
        before = self.write(payload(faces=[(0, 1, 2), (2, 1, 0)]), "before.vmesh")
        after = self.write(name="after.vmesh")
        output = self.root / "certificate.json"
        arguments = ("--before", before, "--after", after, "--source", after, "--output", output)
        self.assertEqual(self.invoke(*arguments), 0)
        original = output.read_bytes()
        result = json.loads(original)
        self.assertTrue(result["passed"])
        self.assertEqual(result["before"]["nondegenerate_duplicate_groups"], 1)
        self.assertTrue(result["source_retention_before"]["retained"])
        self.assertEqual(self.invoke(*arguments), 2)
        self.assertEqual(output.read_bytes(), original)

    def test_cli_failed_source_and_duplicates_write_failed_certificate(self):
        source = self.write(name="source.vmesh")
        after = self.write(payload(faces=[(0, 2, 1), (0, 2, 1)]), "after.vmesh")
        output = self.root / "failed.json"
        self.assertEqual(self.invoke("--before", source, "--after", after,
                                     "--source", source, "--output", output), 1)
        result = json.loads(output.read_text())
        self.assertFalse(result["passed"])
        self.assertEqual(set(result["checks"].values()), {False})

    def test_cli_invalid_input_does_not_publish_certificate(self):
        invalid = self.write(b"bad")
        output = self.root / "invalid.json"
        self.assertEqual(self.invoke("--before", invalid, "--after", invalid, "--output", output), 2)
        self.assertFalse(output.exists())

    def test_cli_without_source_does_not_claim_source_retention(self):
        mesh = self.write()
        output = self.root / "no-source.json"
        self.assertEqual(self.invoke("--before", mesh, "--after", mesh, "--output", output), 0)
        result = json.loads(output.read_text())
        self.assertIsNone(result["source"])
        self.assertIsNone(result["source_retention_after"])
        self.assertEqual(list(result["checks"]), ["after_has_no_exact_duplicate_groups"])

    def test_cli_refuses_existing_dangling_output_symlink(self):
        mesh = self.write()
        output = self.root / "link.json"
        target = self.root / "missing.json"
        output.symlink_to(target)
        self.assertEqual(self.invoke("--before", mesh, "--after", mesh, "--output", output), 2)
        self.assertTrue(output.is_symlink())
        self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
