"""Bounded whole-cycle recovery with exact new-contact checks.

The interval search and angle-bound design descend from the lab's MIT
experimental work on ScrollFiesta. This implementation uses only Python's
standard library, preserves source indices and never welds or moves vertices.
"""
from collections import Counter, defaultdict
from itertools import combinations
import math
from .exact import Triangle, boxes_overlap, pair_check, cross, sub
from .mesh import Mesh

CONDITION = 1.25 / 0.75
TAU = 2 * math.pi
ANGLE_TOL = 1e-9
NODE_CAP = 2000000
PAIR_CAP = 20000000


class BudgetExceeded(Exception):
    pass


def corner_bounds(a, b, c):
    u, v = sub(b, a), sub(c, a)
    area2 = math.hypot(*cross(u, v))
    product = sum(x * y for x, y in zip(u, v))
    if not area2 > 0 or not math.isfinite(area2) or not math.isfinite(product):
        raise ValueError("Invalid corner")
    half = 0.5 * math.atan2(area2, product)
    sine, cosine = math.sin(half), math.cos(half)
    return (2 * math.atan2(sine, CONDITION * cosine),
            2 * math.atan2(CONDITION * sine, cosine))


def edge_index(faces):
    edges = defaultdict(list)
    for f in faces:
        for a, b in zip(f, f[1:] + f[:1]):
            edges[tuple(sorted((a, b)))].append((a, b))
    return edges


def boundary_cycles(mesh):
    """Return only isolated, degree-two oriented source boundary cycles."""
    edges = edge_index(mesh.faces)
    outgoing = defaultdict(list)
    incoming = Counter()
    for incidences in edges.values():
        if len(incidences) == 1:
            a, b = incidences[0]
            outgoing[a].append(b); incoming[b] += 1
    unseen = set(outgoing)
    cycles = []
    while unseen:
        start = min(unseen); current = start; cycle = []
        while current not in cycle:
            unseen.discard(current); cycle.append(current)
            if len(outgoing[current]) != 1 or incoming[current] != 1:
                break
            current = outgoing[current][0]
        else:
            if current == start:
                cycles.append(cycle)
    return cycles


def recover_cycle(mesh, cycle, *, node_budget=NODE_CAP, pair_budget=PAIR_CAP):
    """Return an accepted Mesh or the original Mesh plus an explicit refusal.

    Budget arguments may only reduce the fixed ceilings. Contact checks use
    rational arithmetic of stored coordinate values. Existing source/source
    intersections, anatomical sheet identity and full UV maps are not certified.
    """
    stats = {"accepted": False, "added_faces": 0, "nodes": 0,
             "pair_queries": 0, "exact_pairs": 0, "candidates": 0,
             "source_faces": len(mesh.faces), "source_retained": True}

    def refusal(reason):
        return mesh, dict(stats, reason=reason)

    if type(node_budget) is not int or type(pair_budget) is not int or not 0 <= node_budget <= NODE_CAP or not 0 <= pair_budget <= PAIR_CAP:
        return refusal("invalid_budget")
    if not 3 <= len(cycle) <= 19 or len(set(cycle)) != len(cycle) or any(type(v) is not int or not 0 <= v < len(mesh.vertices) for v in cycle):
        return refusal("invalid_cycle")
    if 2048 * len(mesh.faces) + 512 * len(mesh.vertices) + 969 * 4096 > 128 * 1024**2:
        return refusal("scratch_budget")
    vertices, faces = mesh.vertices, mesh.faces
    edges = edge_index(faces)
    if any(len(row) > 2 or (len(row) == 2 and row[0] != tuple(reversed(row[1]))) for row in edges.values()):
        return refusal("source_edge_topology")
    boundary_degree = Counter(v for row in edges.values() if len(row) == 1 for v in row[0])
    directions = []
    for a, b in zip(cycle, cycle[1:] + cycle[:1]):
        row = edges.get(tuple(sorted((a, b))), [])
        if len(row) != 1 or boundary_degree[a] != 2:
            return refusal("not_an_isolated_source_boundary")
        directions.append(row[0] == (a, b))
    if len(set(directions)) != 1:
        return refusal("inconsistent_boundary_orientation")
    reverse = directions[0]
    source = [Triangle(tuple(vertices[v] for v in f)) for f in faces]
    if any(t.degenerate for t in source):
        return refusal("degenerate_source")
    sums = {v: [0.0, 0.0] for v in cycle}
    try:
        for f in faces:
            for i, v in enumerate(f):
                if v in sums:
                    lo, hi = corner_bounds(vertices[v], vertices[f[(i+1) % 3]], vertices[f[(i+2) % 3]])
                    sums[v][0] += lo; sums[v][1] += hi
    except ValueError:
        return refusal("invalid_source_angle")

    def compatible(a, b):
        if stats["pair_queries"] >= pair_budget:
            raise BudgetExceeded
        stats["pair_queries"] += 1
        if not boxes_overlap(a.box, b.box):
            return True
        stats["exact_pairs"] += 1
        return pair_check(a, b)["allowed"]

    n = len(cycle)
    good = {}
    geometry = {}
    angles = {}
    try:
        for i, k, j in combinations(range(n), 3):
            local = (i, j, k) if reverse else (i, k, j)
            face = tuple(cycle[v] for v in local)
            if any(abs(a-b) not in (1, n-1) and tuple(sorted((cycle[a], cycle[b]))) in edges
                   for a, b in zip(local, local[1:] + local[:1])):
                continue
            tri = Triangle(tuple(vertices[v] for v in face))
            if tri.degenerate:
                continue
            scale = sum(sum((a[d]-b[d])**2 for d in range(3)) for a, b in zip(tri.points, tri.points[1:] + tri.points[:1]))
            area2 = cross(sub(tri.points[1], tri.points[0]), sub(tri.points[2], tri.points[0]))
            if not scale > 0 or not sum(x*x for x in area2) > 1e-12 * scale * scale:
                continue
            if not all(compatible(tri, old) for old in source):
                continue
            bounds = {v: corner_bounds(vertices[v], vertices[face[(h+1) % 3]], vertices[face[(h+2) % 3]]) for h, v in enumerate(face)}
            key = (i, k, j)
            good[key] = face; geometry[key] = tri; angles[key] = bounds
        stats["candidates"] = len(good)
        possible = {(i, i+1) for i in range(n-1)}
        for length in range(2, n):
            for i in range(n-length):
                j = i + length
                if any((i, k, j) in good and (i, k) in possible and (k, j) in possible for k in range(i+1, j)):
                    possible.add((i, j))
        if (0, n-1) not in possible:
            return refusal("no_complete_triangulation")
        pair_cache = {}

        def search(pending, chosen):
            if stats["nodes"] >= node_budget:
                raise BudgetExceeded
            stats["nodes"] += 1
            totals = {v: list(sums[v]) for v in cycle}
            for key in chosen:
                for v, bound in angles[key].items():
                    totals[v][0] += bound[0]; totals[v][1] += bound[1]
            for local, v in enumerate(cycle):
                lo, hi = totals[v]
                open_fan = any(a <= local <= b for a, b in pending)
                if lo > TAU + ANGLE_TOL or (not open_fan and hi < TAU - ANGLE_TOL):
                    return None
            if not pending:
                return chosen if len(chosen) == n-2 else None
            a, b = pending[-1]
            for k in range(a+1, b):
                key = (a, k, b)
                if key not in good or (a, k) not in possible or (k, b) not in possible:
                    continue
                safe = True
                for previous in chosen:
                    pair = tuple(sorted((key, previous)))
                    if pair not in pair_cache:
                        pair_cache[pair] = compatible(geometry[key], geometry[previous])
                    if not pair_cache[pair]:
                        safe = False; break
                if not safe:
                    continue
                next_pending = pending[:-1] + ([(a, k)] if k-a > 1 else []) + ([(k, b)] if b-k > 1 else [])
                answer = search(next_pending, chosen + [key])
                if answer is not None:
                    return answer
            return None

        answer = search([(0, n-1)], [])
        if answer is None:
            return refusal("no_admissible_complete_triangulation")
        addition = tuple(good[key] for key in answer)
        patch_edges = edge_index(addition)
        expected_boundary = {tuple(sorted((a, b))) for a, b in zip(cycle, cycle[1:] + cycle[:1])}
        actual_boundary = {edge for edge, row in patch_edges.items() if len(row) == 1}
        if actual_boundary != expected_boundary or any(len(row) > 2 or (len(row) == 2 and row[0] != tuple(reversed(row[1]))) for row in patch_edges.values()):
            return refusal("patch_boundary_certificate_failed")
        for edge in expected_boundary:
            if patch_edges[edge][0] != tuple(reversed(edges[edge][0])):
                return refusal("patch_orientation_certificate_failed")
        candidate = Mesh(vertices, faces + addition)
        return candidate, dict(stats, accepted=True, added_faces=len(addition),
                               reason="complete_exact_checked_patch",
                               added_indices=addition,
                               angle_condition_bound=CONDITION,
                               limits="No source/source exact audit, full UV parameterization, minimum-clearance, CT-fidelity, anatomy or text certificate.")
    except BudgetExceeded:
        return refusal("budget_exhausted")
    except (ValueError, OverflowError):
        return refusal("invalid_geometry")
