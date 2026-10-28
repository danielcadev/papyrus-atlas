"""Exact, stdlib-only intersection certificate for an added VMESH patch.

Run only through this project's guarded runner. Finite binary32 coordinates
are converted directly to Fraction: no projection rounding or epsilon welding.
Every added/source and added/added pair whose AABBs overlap is checked. The
intersection must be contained in the simplex of their exact common corners.
This deliberately rejects an unindexed edge/vertex contact that has no common
corner; it does not certify source/source pairs or anatomical identity.
"""

import argparse
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
from functools import cached_property
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


class MeshFormatError(ValueError):
    pass


def cyclic_key(triangle):
    return min(triangle, triangle[1:] + triangle[:1], triangle[2:] + triangle[:2])


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2] - a[2]*b[1], a[2]*b[0] - a[0]*b[2],
            a[0]*b[1] - a[1]*b[0])


def interpolate(a, b, t):
    return tuple(x + t * (y - x) for x, y in zip(a, b))


@dataclass
class Triangle:
    points: tuple
    face_index: int = -1

    @cached_property
    def exact(self):
        return tuple(tuple(Fraction(value) for value in p) for p in self.points)

    @cached_property
    def normal(self):
        a, b, c = self.exact
        return cross(sub(b, a), sub(c, a))

    @cached_property
    def box(self):
        return tuple((min(p[d] for p in self.points),
                      max(p[d] for p in self.points)) for d in range(3))

    @property
    def degenerate(self):
        return not any(self.normal)


def read_mesh(path):
    """Read a strictly laid-out VMESH, including validation of unused data."""
    path = Path(path)
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        def read_exact(n):
            data = stream.read(n)
            if len(data) != n:
                raise MeshFormatError(f"{path}: truncated payload")
            digest.update(data)
            return data

        magic, version, endian, flags, hs, nv, nf, vo, uo, fo = HEADER.unpack(
            read_exact(HEADER.size))
        if (magic, version, endian, hs) != (b"VESMESH1", 1, 0x01020304, 64):
            raise MeshFormatError(f"{path}: invalid header")
        if flags & ~3 or (flags & 2 and not flags & 1):
            raise MeshFormatError(f"{path}: invalid flags")
        if not 0 < nv <= (1 << 31) - 1 or nf == 0:
            raise MeshFormatError(f"{path}: invalid counts")
        ve = hs + nv * VERTEX.size
        expected_uo = ve if flags & 1 else 0
        expected_fo = ve + (nv * (16 if flags & 2 else 8) if flags & 1 else 0)
        size = expected_fo + nf * FACE.size
        if (vo != hs or uo != expected_uo or fo != expected_fo
                or size > (1 << 64) - 1 or os.fstat(stream.fileno()).st_size != size):
            raise MeshFormatError(f"{path}: invalid layout/file length")
        vertices = []
        for i in range(nv):
            p = VERTEX.unpack(read_exact(VERTEX.size))
            if not all(map(math.isfinite, p)):
                raise MeshFormatError(f"{path}: nonfinite vertex {i}")
            vertices.append(p)
        if flags & 1:
            uv = struct.Struct("<dd" if flags & 2 else "<ff")
            for i in range(nv):
                if not all(map(math.isfinite, uv.unpack(read_exact(uv.size)))):
                    raise MeshFormatError(f"{path}: nonfinite UV {i}")
        triangles = []
        for i in range(nf):
            indices = FACE.unpack(read_exact(FACE.size))
            if not all(0 <= k < nv for k in indices):
                raise MeshFormatError(f"{path}: invalid face {i}")
            triangles.append(Triangle(tuple(vertices[k] for k in indices), i))
    return triangles, {"path": str(path.resolve()), "sha256": digest.hexdigest(),
                       "vertices": nv, "faces": nf, "flags": flags}


def boxes_overlap(a, b):
    return all(a[d][0] <= b[d][1] and b[d][0] <= a[d][1] for d in range(3))


def unique(points):
    return list(dict.fromkeys(points))


def plane_section(points, distances):
    """Endpoints of the exact triangle/plane intersection, possibly empty."""
    result = [p for p, d in zip(points, distances) if d == 0]
    for i in range(3):
        j = (i + 1) % 3
        if distances[i] * distances[j] < 0:
            result.append(interpolate(points[i], points[j],
                                      distances[i] / (distances[i] - distances[j])))
    return unique(result)


def strict_same_side(distances):
    return all(d > 0 for d in distances) or all(d < 0 for d in distances)


def coplanar_intersection(a, b, normal):
    """Exact convex clipping, retaining point/segment contacts as well."""
    drop = next(d for d in range(3) if normal[d] != 0)
    axes = [d for d in range(3) if d != drop]

    def orient(u, v, p):
        i, j = axes
        return (v[i]-u[i])*(p[j]-u[j]) - (v[j]-u[j])*(p[i]-u[i])

    sign = 1 if orient(*b) > 0 else -1
    polygon = list(a)
    for i in range(3):
        if not polygon:
            break
        u, v = b[i], b[(i+1) % 3]
        result = []
        prev = polygon[-1]
        dp = sign * orient(u, v, prev)
        for cur in polygon:
            dc = sign * orient(u, v, cur)
            if (dp >= 0) != (dc >= 0):
                result.append(interpolate(prev, cur, dp / (dp-dc)))
            if dc >= 0:
                result.append(cur)
            prev, dp = cur, dc
        polygon = unique(result)
    return polygon


def intersection_vertices(a, b):
    """Vertices of the exact convex intersection of two nondegenerate tris."""
    if a.degenerate or b.degenerate:
        raise ValueError("intersection predicate requires nondegenerate triangles")
    pa, pb, na, nb = a.exact, b.exact, a.normal, b.normal
    db = [dot(na, sub(p, pa[0])) for p in pb]
    da = [dot(nb, sub(p, pb[0])) for p in pa]
    if strict_same_side(db) or strict_same_side(da):
        return []
    if all(d == 0 for d in db):
        return coplanar_intersection(pa, pb, na)
    direction = cross(na, nb)
    if not any(direction):
        return []  # Distinct parallel planes.
    sa, sb = plane_section(pa, da), plane_section(pb, db)
    if not sa or not sb:
        return []
    axis = next(d for d in range(3) if direction[d] != 0)
    sa.sort(key=lambda p: p[axis])
    sb.sort(key=lambda p: p[axis])
    lo = max(sa[0][axis], sb[0][axis])
    hi = min(sa[-1][axis], sb[-1][axis])
    if lo > hi:
        return []

    def at(value):
        if len(sa) == 1:
            return sa[0]
        return interpolate(sa[0], sa[-1],
                           (value-sa[0][axis]) / (sa[-1][axis]-sa[0][axis]))

    return unique([at(lo), at(hi)])


def intersection_dimension(points):
    if not points:
        return -1
    if len(points) == 1:
        return 0
    base = sub(points[1], points[0])
    return 2 if any(any(cross(base, sub(p, points[0]))) for p in points[2:]) else 1


def point_on_segment(p, a, b):
    return not any(cross(sub(p, a), sub(b, a))) and dot(sub(p, a), sub(p, b)) <= 0


def pair_check(a, b):
    """Reject intersections beyond the simplex of exact common corner points."""
    points = intersection_vertices(a, b)
    common = sorted(set(a.exact) & set(b.exact))
    if not points:
        allowed = True
    elif len(common) == 1:
        allowed = all(p == common[0] for p in points)
    elif len(common) == 2:
        allowed = all(point_on_segment(p, *common) for p in points)
    else:
        allowed = False
    return {"allowed": allowed, "shared_corners": len(common),
            "intersection_dimension": intersection_dimension(points),
            "reason": ("allowed_common_simplex" if allowed else
                       "duplicate_geometry" if len(common) == 3 else
                       "intersection_outside_common_simplex"),
            "intersection_vertices_rational": [[str(x) for x in p] for p in points]}


def make_certificate(source_path, candidate_path):
    source, source_report = read_mesh(source_path)
    candidate, candidate_report = read_mesh(candidate_path)
    remaining = Counter(cyclic_key(t.points) for t in source)
    added = []
    for t in candidate:
        key = cyclic_key(t.points)
        if remaining[key] > 0:
            remaining[key] -= 1
        else:
            added.append(t)
    missing = sum(remaining.values())
    bad_source = [t.face_index for t in source if t.degenerate]
    bad_added = [t.face_index for t in added if t.degenerate]
    aabb_pairs = exact_pairs = conflicts = 0
    examples = []

    def inspect(a, b, kind):
        nonlocal aabb_pairs, exact_pairs, conflicts
        if not boxes_overlap(a.box, b.box):
            return
        aabb_pairs += 1
        if a.degenerate or b.degenerate:
            return  # Explicitly failed separately; no unsupported false pass.
        exact_pairs += 1
        result = pair_check(a, b)
        if not result["allowed"]:
            conflicts += 1
            if len(examples) < 100:
                examples.append({"pair_kind": kind, "candidate_face": a.face_index,
                                 "other_face": b.face_index, **result})

    for i, triangle in enumerate(added):
        for original in source:
            inspect(triangle, original, "added/source")
        for previous in added[:i]:
            inspect(triangle, previous, "added/added")
    checks = {"source_multiplicity_and_cyclic_orientation_preserved": missing == 0,
              "source_nondegenerate_for_supported_predicate": not bad_source,
              "added_triangles_nondegenerate": not bad_added,
              "no_intersection_outside_exact_common_simplex": conflicts == 0}
    return {"schema": "exact-patch-intersections-v1", "passed": all(checks.values()),
            "checks": checks, "source": source_report, "candidate": candidate_report,
            "missing_or_reoriented_source_faces": missing,
            "added_faces": len(added), "added_candidate_face_indices": [t.face_index for t in added],
            "source_degenerate_face_indices": bad_source,
            "added_degenerate_face_indices": bad_added,
            "potential_pairs": len(added)*len(source) + len(added)*(len(added)-1)//2,
            "aabb_overlapping_pairs": aabb_pairs, "exact_pairs_checked": exact_pairs,
            "conflicts": conflicts, "conflict_examples": examples,
            "conflict_examples_truncated": conflicts > len(examples),
            "method": {"coordinate_space": "stored global ZYX binary32",
                       "arithmetic": "exact fractions of stored binary32 coordinates",
                       "tolerance": 0, "native_geometry_imports": False,
                       "source_key": "oriented coordinate multiset modulo cyclic rotations",
                       "allowed_contact": "subset of exact common-corner simplex"},
            "limits": ["Source/source pairs are not audited.",
                       "No boundary, topology, angle-fan, winding-field, coverage or anatomical identity certificate.",
                       "Unindexed contact without common corner coordinates is rejected conservatively.",
                       "Zero added faces can pass; passing alone does not prove a hole was closed.",
                       "Only saved binary32 geometry is certified, with no minimum-clearance claim."]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.output.exists():
            raise FileExistsError(f"Preserve existing output: {args.output}")
        report = make_certificate(args.source, args.candidate)
        with args.output.open("x") as stream:
            json.dump(report, stream, indent=2)
            stream.write("\n")
    except (OSError, ValueError, OverflowError, struct.error) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps({"passed": report["passed"], "added_faces": report["added_faces"],
                      "exact_pairs_checked": report["exact_pairs_checked"],
                      "conflicts": report["conflicts"], "output": str(args.output)}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
