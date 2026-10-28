"""Certify continuous bidirectional coverage of two saved added patches.

Run only through the project's guarded runner. --source is the shared retained
mesh; subtract its oriented coordinate multiset from --before and --after.
Only the resulting patches require subdivision. By default they are compared
with each other; --include-retained-background instead compares each patch
with the opposite full surface. Shared retained geometry is then covered
trivially by the exact source-retention check. An exact per-root AABB filter
keeps every target triangle that could be within delta of that root.

For a source microtriangle, c is its centroid and R its enclosing radius about
c. A rational barycentric point q in a target triangle proves full coverage if
||c-q|| + R <= delta. The test is exact over Fraction and has no square roots:
t=delta**2-D**2-R**2 >= 0 and t*t >= 4*D**2*R**2. Midpoint subdivision covers
the entire original triangle. An exact identical-triangle witness is also used.
Failure to finish this sufficient test is INCONCLUSIVE, not a counterexample.
"""

import argparse
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
import json
import math
from pathlib import Path
import resource
import sys

from exact_patch_intersections import Triangle, cyclic_key, dot, read_mesh, sub


BARYCENTRIC_DENOMINATOR = 1 << 24


@dataclass(frozen=True)
class Budget:
    max_cells: int = 250000
    max_depth: int = 16
    max_witnesses: int = 100000
    max_pending_cells: int = 4096
    max_memory_mib: int = 192

    def validate(self):
        if (self.max_cells < 1 or self.max_depth < 0 or self.max_witnesses < 1
                or self.max_pending_cells < 1 or self.max_memory_mib < 1):
            raise ValueError("budgets must be positive; max_depth may be zero")

    def report(self):
        return {"max_cells_per_direction": self.max_cells, "max_depth": self.max_depth,
                "max_witnesses_per_direction": self.max_witnesses,
                "max_pending_cells_per_direction": self.max_pending_cells,
                "max_process_peak_rss_mib": self.max_memory_mib,
                "memory_check_interval_cells": 128}


def peak_memory_mib():
    # The project runs on Linux; ru_maxrss is KiB, and includes this process
    # only. The external systemd guard remains the authoritative hard limit.
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def geom_key(triangle):
    return tuple(sorted(triangle.points))


def unique_triangles(triangles):
    result = {}
    for triangle in triangles:
        result.setdefault(geom_key(triangle), triangle)
    return list(result.values())


def extract_patch(source, full):
    """Retain orientation and multiplicity during subtraction, even duplicates."""
    remaining = Counter(cyclic_key(t.points) for t in source)
    added = []
    for triangle in full:
        key = cyclic_key(triangle.points)
        if remaining[key] > 0:
            remaining[key] -= 1
        else:
            added.append(triangle)
    return added, sum(remaining.values())


def boxes_within_delta(a, b, delta_squared):
    """Conservative target filter: exact lower distance between two AABBs.

    Stored endpoints are exact binary32 values. Subtract after converting to
    Fraction, so a triangle exactly at the threshold cannot be rounded out.
    """
    lower_squared = Fraction(0)
    for d in range(3):
        if a[d][0] > b[d][1]:
            gap = Fraction(a[d][0])-Fraction(b[d][1])
        elif b[d][0] > a[d][1]:
            gap = Fraction(b[d][0])-Fraction(a[d][1])
        else:
            continue
        lower_squared += gap*gap
        if lower_squared > delta_squared:
            return False
    return True


def enclosing_ball(cell):
    center = tuple(sum(p[d] for p in cell) / 3 for d in range(3))
    radius_squared = max(dot(sub(p, center), sub(p, center)) for p in cell)
    return center, radius_squared


def ball_covers(distance_squared, radius_squared, delta_squared):
    if min(distance_squared, radius_squared, delta_squared) < 0:
        raise ValueError("squared quantities must be nonnegative")
    t = delta_squared - distance_squared - radius_squared
    return t >= 0 and t*t >= 4*distance_squared*radius_squared


def subdivide(cell):
    a, b, c = cell
    midpoint = lambda p, q: tuple((x+y)/2 for x, y in zip(p, q))
    ab, bc, ca = midpoint(a, b), midpoint(b, c), midpoint(c, a)
    return ((a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca))


def float_closest_weights(point, triangle):
    """Heuristic only: edge projections and an interior plane projection.

    Its floating arithmetic never certifies a distance. Any returned weights
    are quantized into the simplex before the exact acceptance predicate.
    """
    vertices = triangle.points
    candidates = []
    for i, j in ((0, 1), (1, 2), (2, 0)):
        edge = sub(vertices[j], vertices[i])
        denominator = dot(edge, edge)
        t = max(0.0, min(1.0, dot(sub(point, vertices[i]), edge) / denominator)) if denominator > 0 else 0.0
        weights = [0.0, 0.0, 0.0]
        weights[i], weights[j] = 1-t, t
        candidates.append(tuple(weights))
    a, b, c = vertices
    ab, ac, ap = sub(b, a), sub(c, a), sub(point, a)
    d00, d01, d11 = dot(ab, ab), dot(ab, ac), dot(ac, ac)
    d20, d21 = dot(ap, ab), dot(ap, ac)
    denominator = d00*d11-d01*d01
    if denominator > 0 and math.isfinite(denominator):
        v, w = (d11*d20-d01*d21)/denominator, (d00*d21-d01*d20)/denominator
        if v >= 0 and w >= 0 and v+w <= 1:
            candidates.append((1-v-w, v, w))

    def squared_distance(weights):
        q = tuple(sum(weights[i]*vertices[i][d] for i in range(3)) for d in range(3))
        return dot(sub(point, q), sub(point, q))

    return min(candidates, key=squared_distance)


def rational_weights(weights):
    """Round into an explicitly nonnegative rational simplex, without epsilon."""
    denominator = BARYCENTRIC_DENOMINATOR
    first = max(0, min(denominator, int(weights[0]*denominator)))
    second = max(0, min(denominator-first, int(weights[1]*denominator)))
    return first, second, denominator-first-second


def rational_target_point(triangle, weights):
    return tuple(sum(weights[i]*triangle.exact[i][d] for i in range(3)) /
                 BARYCENTRIC_DENOMINATOR for d in range(3))


def find_witness(center, radius_squared, targets, delta_squared):
    if radius_squared > delta_squared:
        return None
    center_float = tuple(float(x) for x in center)
    ranked = []
    for triangle in targets:
        weights = rational_weights(float_closest_weights(center_float, triangle))
        # This ordering is only a heuristic. Every candidate ultimately uses
        # exact barycentric coordinates and exact squared distances.
        q_float = tuple(sum(weights[i]*triangle.points[i][d] for i in range(3)) /
                        BARYCENTRIC_DENOMINATOR for d in range(3))
        approximate = dot(sub(center_float, q_float), sub(center_float, q_float))
        ranked.append((approximate, triangle.face_index, triangle, weights))
    ranked.sort(key=lambda item: (item[0], item[1]))
    for _, _, triangle, weights in ranked:
        q = rational_target_point(triangle, weights)
        distance_squared = dot(sub(center, q), sub(center, q))
        if ball_covers(distance_squared, radius_squared, delta_squared):
            return triangle.face_index, weights, distance_squared
    return None


def certify_direction(source_triangles, target_triangles, delta, budget, filter_target_boxes=False):
    """A finite sufficient proof; budget exhaustion is explicitly inconclusive."""
    budget.validate()
    if delta < 0:
        raise ValueError("delta must be nonnegative")
    sources, targets = unique_triangles(source_triangles), unique_triangles(target_triangles)
    target_by_geometry = {geom_key(t): t for t in targets}
    stack = [(t, t.exact, "", 0) for t in reversed(sources)]
    targets_by_root = {}
    filter_pairs = 0
    filter_counts = []
    witnesses = []
    visited = subdivisions = max_depth_seen = 0
    max_pending = len(stack)
    max_d2 = max_r2 = Fraction(0)
    termination = "certified"
    unresolved = 0
    if peak_memory_mib() > budget.max_memory_mib:
        termination, unresolved = "inconclusive_memory_limit", len(stack)
    if filter_target_boxes and termination == "certified":
        for root in sources:
            selected = []
            for target in targets:
                if filter_pairs % 128 == 0 and peak_memory_mib() > budget.max_memory_mib:
                    termination, unresolved = "inconclusive_memory_limit", len(stack)
                    break
                filter_pairs += 1
                if boxes_within_delta(root.box, target.box, delta*delta):
                    selected.append(target)
            targets_by_root[id(root)] = selected
            filter_counts.append({"source_face_index": root.face_index,
                                  "target_geometries_after_filter": len(selected)})
            if termination != "certified":
                break
    if sources and not targets and termination == "certified":
        termination, unresolved = "inconclusive_empty_target", len(stack)
    elif len(stack) > budget.max_pending_cells and termination == "certified":
        termination, unresolved = "inconclusive_pending_cell_limit", len(stack)
    while stack and termination == "certified":
        if visited >= budget.max_cells:
            termination, unresolved = "inconclusive_cell_limit", len(stack)
            break
        if (visited % 128 == 0 and peak_memory_mib() > budget.max_memory_mib):
            termination, unresolved = "inconclusive_memory_limit", len(stack)
            break
        root, cell, path, depth = stack.pop()
        visited += 1
        max_depth_seen = max(max_depth_seen, depth)
        identical = target_by_geometry.get(geom_key(root)) if depth == 0 else None
        if identical is not None:
            witness = [root.face_index, path, identical.face_index, "identical"]
        else:
            center, radius_squared = enclosing_ball(cell)
            relevant_targets = targets_by_root[id(root)] if filter_target_boxes else targets
            found = find_witness(center, radius_squared, relevant_targets, delta*delta)
            if found is not None:
                target_index, weights, distance_squared = found
                witness = [root.face_index, path, target_index, *weights]
                max_d2 = max(max_d2, distance_squared)
                max_r2 = max(max_r2, radius_squared)
            else:
                witness = None
        if witness is not None:
            if len(witnesses) >= budget.max_witnesses:
                termination, unresolved = "inconclusive_witness_limit", len(stack)+1
                break
            witnesses.append(witness)
            continue
        if depth >= budget.max_depth:
            termination, unresolved = "inconclusive_depth_limit", len(stack)+1
            break
        if len(stack)+4 > budget.max_pending_cells:
            termination, unresolved = "inconclusive_pending_cell_limit", len(stack)+1
            break
        children = subdivide(cell)
        for i in reversed(range(4)):
            stack.append((root, children[i], path+str(i), depth+1))
        max_pending = max(max_pending, len(stack))
        subdivisions += 1
    if termination == "certified" and peak_memory_mib() > budget.max_memory_mib:
        termination, unresolved = "inconclusive_memory_limit", len(stack)
    return {"certified": termination == "certified" and not stack,
            "termination": termination, "input_source_faces": len(source_triangles),
            "unique_source_geometries": len(sources), "input_target_faces": len(target_triangles),
            "unique_target_geometries": len(targets), "visited_cells": visited,
            "subdivisions": subdivisions, "certified_leaf_cells": len(witnesses),
            "maximum_depth_seen": max_depth_seen, "maximum_pending_cells": max_pending,
            "exact_target_aabb_filter_enabled": filter_target_boxes,
            "target_aabb_filter_pairs": filter_pairs,
            "target_aabb_filter_by_root": filter_counts,
            "unresolved_frontier_cells_at_stop": unresolved,
            "largest_accepted_centroid_distance_squared": str(max_d2),
            "largest_accepted_cell_radius_squared": str(max_r2),
            "peak_process_rss_mib_at_end": peak_memory_mib(), "witnesses": witnesses}


def make_certificate(before_path, source_path, after_path, delta=Fraction(1, 4), budget=Budget(),
                     include_retained_background=False):
    budget.validate()
    if delta < 0:
        raise ValueError("delta must be nonnegative")
    source, source_report = read_mesh(source_path)
    before, before_report = read_mesh(before_path)
    after, after_report = read_mesh(after_path)
    old_patch, missing_before = extract_patch(source, before)
    new_patch, missing_after = extract_patch(source, after)
    if missing_before or missing_after:
        directions = None
        passed = False
        status = "invalid_source_retention"
    else:
        if include_retained_background:
            # Use triangles from the actual opposite full file so exported
            # target face indices remain correct even if source IDs/order differ.
            directions = {"before_patch_to_after_surface": certify_direction(old_patch, after, delta, budget, True),
                          "after_patch_to_before_surface": certify_direction(new_patch, before, delta, budget, True)}
        else:
            directions = {"before_patch_to_after_patch": certify_direction(old_patch, new_patch, delta, budget),
                          "after_patch_to_before_patch": certify_direction(new_patch, old_patch, delta, budget)}
        passed = all(direction["certified"] for direction in directions.values())
        status = "certified" if passed else "inconclusive"
    return {"schema": "continuous-patch-coverage-v2", "passed": passed, "status": status,
            "delta_exact": str(delta), "delta_squared_exact": str(delta*delta),
            "coordinate_space": "stored global ZYX binary32; no tolerance weld",
            "source": source_report, "before": before_report, "after": after_report,
            "missing_or_reoriented_source_faces_before": missing_before,
            "missing_or_reoriented_source_faces_after": missing_after,
            "before_patch_face_indices": [t.face_index for t in old_patch],
            "after_patch_face_indices": [t.face_index for t in new_patch],
            "before_patch_faces": len(old_patch), "after_patch_faces": len(new_patch),
            "include_retained_background": include_retained_background,
            "retained_background_coverage": ("Exact shared oriented source multiset is present in both surfaces; distance zero."
                                             if include_retained_background and not missing_before and not missing_after else None),
            "budget_declared_before_geometry_checks": budget.report(), "directions": directions,
            "proof": {
                "pointwise_scope": ("every point of both full surfaces: explicit patch proofs plus identical retained source"
                                    if include_retained_background else "every point of both closed triangular patch unions"),
                "bound": "distance(c,q)+max_vertex_distance(c) <= delta",
                "exact_test": "t=delta^2-D^2-R^2 >= 0 and t^2 >= 4*D^2*R^2",
                "q_membership": "nonnegative integer barycentric weights summing to the denominator",
                "barycentric_denominator": BARYCENTRIC_DENOMINATOR,
                "witness_fields": ["source full-mesh face index", "subdivision path", "target full-mesh face index", "weight0", "weight1", "weight2"],
                "identical_witness": "[source_index, empty_path, target_index, 'identical'] means exact unordered corners match",
                "subdivision_children": ["(a,ab,ca)", "(ab,b,bc)", "(ca,bc,c)", "(ab,bc,ca)"],
                "subdivision_midpoints": "ab=(a+b)/2, bc=(b+c)/2, ca=(c+a)/2 exactly",
                "geometry_deduplication": "unordered exact corner triples; orientation/multiplicity retained before extraction",
                "target_filter_when_background_included": "retain target if exact squared AABB distance to source root AABB <= delta^2",
                "floating_arithmetic": "nearest-point heuristic and ordering only; never used for acceptance"},
            "limits": [
                "Inconclusive means the sufficient proof did not finish; it is not a distance counterexample.",
                "At an exact delta separation, positive-area parallel triangles may remain inconclusive at every finite depth.",
                "This proves a distance bound, not equal area, identical surfaces, topology, no intersections or anatomical/fibre identity.",
                "Only added patches require subdivision. In background mode their targets are the opposite full surface, and retained source has exact zero distance.",
                "The hard 384 MiB limit, desktop reserve and CPU/GPU restrictions must be supplied by the project guard."]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--after", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--delta", default="0.25", type=Fraction)
    parser.add_argument("--include-retained-background", action="store_true",
                        help="prove full-surface coverage using retained source as an additional target")
    parser.add_argument("--max-cells", type=int, default=Budget.max_cells)
    parser.add_argument("--max-depth", type=int, default=Budget.max_depth)
    parser.add_argument("--max-witnesses", type=int, default=Budget.max_witnesses)
    parser.add_argument("--max-pending-cells", type=int, default=Budget.max_pending_cells)
    parser.add_argument("--max-memory-mib", type=int, default=Budget.max_memory_mib)
    args = parser.parse_args(argv)
    budget = Budget(args.max_cells, args.max_depth, args.max_witnesses,
                    args.max_pending_cells, args.max_memory_mib)
    try:
        budget.validate()
        if args.output.exists():
            raise FileExistsError(f"Preserve existing output: {args.output}")
        report = make_certificate(args.before, args.source, args.after, args.delta, budget,
                                  args.include_retained_background)
        with args.output.open("x") as stream:
            json.dump(report, stream, indent=2)
            stream.write("\n")
    except (OSError, ValueError, OverflowError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps({"passed": report["passed"], "status": report["status"],
                      "delta_exact": report["delta_exact"],
                      "before_patch_faces": report["before_patch_faces"],
                      "after_patch_faces": report["after_patch_faces"],
                      "output": str(args.output)}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
