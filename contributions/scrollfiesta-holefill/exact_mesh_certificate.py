"""Independent, stdlib-only certificate for saved global-ZYX VESMESH1 files.

Compares the exact stored float32 coordinates, with no welding or tolerance.
Signed zeros denote the same coordinate. Cyclic rotations preserve orientation;
reversing a nondegenerate triangle does not. Memory use is O(vertices + faces),
intended for the saved small fixtures, not whole-scroll meshes.

Run through the project's guarded runner. Exit 0 means the stated checks pass,
1 means a valid-input certificate failed, and 2 means input/output was invalid.
This is not a general intersection, manifold, or anatomical-identity auditor.
"""

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import sys


HEADER = struct.Struct("<8sIIIIQQQQQ")
VERTEX = struct.Struct("<fff")
FACE = struct.Struct("<iii")
HAS_UV = 1
UV_F64 = 2
UINT64_MAX = (1 << 64) - 1
FLOAT32_SCALE = 1 << 149


class MeshFormatError(ValueError):
    """The file is not a finite, strictly laid-out VESMESH1 container."""


def cyclic_key(triangle):
    """Canonicalize only the three orientation-preserving rotations."""
    return min(triangle, triangle[1:] + triangle[:1], triangle[2:] + triangle[:2])


def is_degenerate(triangle):
    """Exact zero-area test for finite float32 points, without float products."""
    # Every finite binary32 is an integer multiple of 2**-149. Python integers
    # avoid cancellation/underflow and overflow even for extreme binary32s.
    points = []
    for vertex in triangle:
        point = []
        for value in vertex:
            numerator, denominator = value.as_integer_ratio()
            point.append(numerator * (FLOAT32_SCALE // denominator))
        points.append(point)
    u = [points[1][i] - points[0][i] for i in range(3)]
    v = [points[2][i] - points[0][i] for i in range(3)]
    return (u[1] * v[2] == u[2] * v[1]
            and u[2] * v[0] == u[0] * v[2]
            and u[0] * v[1] == u[1] * v[0])


@dataclass
class MeshFacts:
    report: dict
    oriented_faces: Counter


def inspect_mesh(path):
    """Strictly read one mesh; retain exact oriented face multiplicities."""
    path = Path(path)
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        def read_exact(size):
            payload = stream.read(size)
            if len(payload) != size:
                raise MeshFormatError(f"{path}: truncated payload")
            digest.update(payload)
            return payload

        fields = HEADER.unpack(read_exact(HEADER.size))
        magic, version, endian, flags, header_size, nv, nf, vo, uo, fo = fields
        if (magic, version, endian, header_size) != (
                b"VESMESH1", 1, 0x01020304, HEADER.size):
            raise MeshFormatError(f"{path}: invalid magic/version/endian/header size")
        if flags & ~(HAS_UV | UV_F64) or (flags & UV_F64 and not flags & HAS_UV):
            raise MeshFormatError(f"{path}: unsupported or inconsistent flags")
        if nv == 0 or nf == 0 or nv > (1 << 31) - 1:
            raise MeshFormatError(f"{path}: invalid vertex/face count")
        vertex_end = HEADER.size + nv * VERTEX.size
        uv_size = 16 if flags & UV_F64 else 8
        expected_uo = vertex_end if flags & HAS_UV else 0
        expected_fo = vertex_end + (nv * uv_size if flags & HAS_UV else 0)
        expected_size = expected_fo + nf * FACE.size
        if (expected_size > UINT64_MAX or vo != HEADER.size
                or uo != expected_uo or fo != expected_fo):
            raise MeshFormatError(f"{path}: invalid offsets/layout or size overflow")
        if os.fstat(stream.fileno()).st_size != expected_size:
            raise MeshFormatError(f"{path}: file length differs from exact layout")

        vertices = []
        for index in range(nv):
            vertex = VERTEX.unpack(read_exact(VERTEX.size))
            if not all(map(math.isfinite, vertex)):
                raise MeshFormatError(f"{path}: nonfinite vertex {index}")
            vertices.append(vertex)
        if flags & HAS_UV:
            uv_struct = struct.Struct("<dd" if flags & UV_F64 else "<ff")
            for index in range(nv):
                uv = uv_struct.unpack(read_exact(uv_struct.size))
                if not all(map(math.isfinite, uv)):
                    raise MeshFormatError(f"{path}: nonfinite UV {index}")

        oriented = Counter()
        groups = {}
        for face_index in range(nf):
            face = FACE.unpack(read_exact(FACE.size))
            if not all(0 <= index < nv for index in face):
                raise MeshFormatError(f"{path}: invalid index in face {face_index}")
            triangle = tuple(vertices[index] for index in face)
            oriented[cyclic_key(triangle)] += 1
            groups.setdefault(tuple(sorted(triangle)), []).append(face_index)
        if stream.read(1):
            raise MeshFormatError(f"{path}: trailing bytes")

    duplicates = []
    degenerate_faces = 0
    for triangle, face_indices in groups.items():
        degenerate = is_degenerate(triangle)
        if degenerate:
            degenerate_faces += len(face_indices)
        if len(face_indices) > 1:
            duplicates.append({
                "face_indices": face_indices,
                "global_zyx_vertices": triangle,
                "degenerate": degenerate,
            })
    degenerate_groups = sum(group["degenerate"] for group in duplicates)
    report = {
        "path": str(path.resolve()),
        "sha256": digest.hexdigest(),
        "vertices": nv,
        "faces": nf,
        "flags": flags,
        "format_valid": True,
        "finite_coordinates_and_uv": True,
        "exact_duplicate_groups": len(duplicates),
        "nondegenerate_duplicate_groups": len(duplicates) - degenerate_groups,
        "degenerate_duplicate_groups": degenerate_groups,
        "duplicate_extra_faces": sum(len(g["face_indices"]) - 1 for g in duplicates),
        "degenerate_faces": degenerate_faces,
        "duplicate_groups": duplicates,
    }
    return MeshFacts(report, oriented)


def source_retention(source, target):
    """A multiset inclusion test, including cyclic orientation."""
    missing = source.oriented_faces - target.oriented_faces
    return {
        "retained": not missing,
        "missing_or_reoriented_faces": sum(missing.values()),
        "missing_or_reoriented_distinct_faces": len(missing),
        "missing": [
            {"global_zyx_vertices": triangle, "multiplicity": count}
            for triangle, count in sorted(missing.items())
        ],
    }


def make_certificate(before_path, after_path, source_path=None):
    """Report all duplicate groups and, optionally, source multiset retention."""
    source = inspect_mesh(source_path) if source_path is not None else None
    before = inspect_mesh(before_path)
    before_retention = source_retention(source, before) if source else None
    before_report = before.report
    del before
    after = inspect_mesh(after_path)
    after_retention = source_retention(source, after) if source else None
    checks = {"after_has_no_exact_duplicate_groups": after.report["exact_duplicate_groups"] == 0}
    if source:
        checks["after_retains_source_multiplicity_and_cyclic_orientation"] = after_retention["retained"]
    return {
        "schema": "exact-mesh-certificate-v1",
        "passed": all(checks.values()),
        "checks": checks,
        "before": before_report,
        "after": after.report,
        "source": source.report if source else None,
        "source_retention_before": before_retention,
        "source_retention_after": after_retention,
        "comparison": {
            "face_count_delta": after.report["faces"] - before_report["faces"],
            "duplicate_group_delta": after.report["exact_duplicate_groups"] - before_report["exact_duplicate_groups"],
        },
        "method": {
            "coordinate_space": "saved global ZYX float32",
            "coordinate_tolerance": 0,
            "signed_zero": "positive and negative zero are the same coordinate",
            "duplicate_key": "unordered exact vertex-coordinate multiset; IDs and winding ignored",
            "source_key": "exact ordered coordinates modulo cyclic rotation, with multiplicity",
            "degeneracy": "exact integer cross product after scaling binary32 coordinates by 2**149",
            "native_geometry_imports": False,
        },
        "limits": [
            "Checks saved float32 coordinates only; no epsilon weld or inference about pre-rounding geometry.",
            "Duplicates mean identical vertex-coordinate multisets, not all coincident or intersecting surfaces.",
            "No general triangle-intersection, manifold, minimum-separation, or anatomical sheet-identity certification.",
            "Source inclusion is checked only when --source is supplied; it does not certify every before face survives.",
            "Degenerate faces are reported; isolated degenerate faces alone do not fail the stated duplicate/source checks.",
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", required=True, type=Path)
    parser.add_argument("--after", required=True, type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        # lexists also refuses a preexisting dangling symlink. The exclusive
        # open below is still necessary to protect against a creation race.
        if os.path.lexists(args.output):
            raise FileExistsError(f"Refusing to overwrite {args.output}")
        result = make_certificate(args.before, args.after, args.source)
        encoded = json.dumps(result, indent=2, allow_nan=False) + "\n"
        with args.output.open("x", encoding="utf-8") as output:
            output.write(encoded)
    except (OSError, ValueError) as error:
        print(f"exact_mesh_certificate: {error}", file=sys.stderr)
        return 2
    print(json.dumps({"output": str(args.output.resolve()), "passed": result["passed"],
                      "checks": result["checks"]}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
