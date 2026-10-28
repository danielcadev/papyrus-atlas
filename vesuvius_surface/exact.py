"""Exact rational triangle contacts, reused from the lab's preserved auditor.
No native or third-party imports. See ATTRIBUTION.md.
"""
from dataclasses import dataclass
from fractions import Fraction
from functools import cached_property

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


