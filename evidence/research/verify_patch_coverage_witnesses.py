"""Replay an exported continuous coverage certificate without any search.

Run only through research/run_holefill_guarded.sh. Default expected count is
3303 for continuous-coverage-02.json. No nearest-point heuristic, AABB search,
adaptive search or code from certify_patch_coverage.py is called. This checker
shares only the strict VMESH wire reader with exact_patch_intersections.py.

Every root must have a prefix-free, complete quadtree partition. Every exported
point is reconstructed by integer barycentric weights and checked with exact
Fraction arithmetic. The accepted claim is Hausdorff <= 1/4 for the two full
triangle unions, using their exact retained common source. All failures close
the certificate; a verifier budget failure is not a geometric counterexample.
"""

import argparse
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import resource
import struct
import sys

from exact_patch_intersections import read_mesh


DENOMINATOR = 1 << 24
DELTA = Fraction(1, 4)
DIRECTION_NAMES = ("before_patch_to_after_surface", "after_patch_to_before_surface")


class ReplayFailure(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ReplayFailure(message)


def strict_integer(value, name, minimum=0):
    require(type(value) is int and value >= minimum, f"{name}: invalid integer")
    return value


@dataclass(frozen=True)
class Budget:
    max_witnesses: int = 100000
    max_depth: int = 64
    max_memory_mib: int = 192
    max_json_bytes: int = 8 * 1024 * 1024
    max_mesh_vertices: int = 100000
    max_mesh_faces: int = 100000

    def validate(self):
        for name, value in self.__dict__.items():
            strict_integer(value, name, 1)


def peak_memory_mib():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def check_memory(budget):
    require(peak_memory_mib() <= budget.max_memory_mib,
            "inconclusive: verifier process memory budget exceeded")


def unique_json_keys(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_certificate(path, budget):
    path = Path(path)
    require(path.stat().st_size <= budget.max_json_bytes, "certificate JSON exceeds byte budget")
    raw = path.read_bytes()
    require(len(raw) <= budget.max_json_bytes, "certificate JSON grew beyond byte budget")
    certificate = json.loads(raw, object_pairs_hook=unique_json_keys)
    require(type(certificate) is dict, "certificate must be a JSON object")
    check_memory(budget)
    return certificate, hashlib.sha256(raw).hexdigest()


def bounded_mesh(path, declared, budget):
    require(type(declared) is dict, "missing mesh declaration")
    path = Path(path)
    with path.open("rb") as stream:
        header = stream.read(64)
    require(len(header) == 64, f"{path}: truncated header")
    fields = struct.unpack("<8sIIIIQQQQQ", header)
    require(fields[5] <= budget.max_mesh_vertices, f"{path}: vertex budget exceeded")
    require(fields[6] <= budget.max_mesh_faces, f"{path}: face budget exceeded")
    mesh, actual = read_mesh(path)
    for field in ("sha256", "vertices", "faces", "flags"):
        require(actual[field] == declared.get(field), f"{path}: declared {field} mismatch")
    check_memory(budget)
    return mesh, actual


def oriented_key(points):
    rotations = [points[i:] + points[:i] for i in range(3)]
    return min(rotations)


def geometry_key(points):
    return tuple(sorted(points))


def source_subtraction(source_counts, full):
    used = Counter()
    patch = []
    for triangle in full:
        key = oriented_key(triangle.points)
        if used[key] < source_counts[key]:
            used[key] += 1
        else:
            patch.append(triangle)
    missing = sum((source_counts-used).values())
    require(missing == 0, f"source geometry, multiplicity or orientation lost: {missing} face(s)")
    return patch


def root_representatives(patch):
    representatives = {}
    for triangle in patch:
        representatives.setdefault(geometry_key(triangle.points), triangle)
    return {triangle.face_index: triangle for triangle in representatives.values()}


def exact_points(triangle):
    return tuple(tuple(Fraction(coordinate) for coordinate in p) for p in triangle.points)


def reconstruct_cell(root, path):
    a, b, c = root
    for digit in path:
        ab = tuple((a[d]+b[d])/2 for d in range(3))
        bc = tuple((b[d]+c[d])/2 for d in range(3))
        ca = tuple((c[d]+a[d])/2 for d in range(3))
        if digit == "0":
            a, b, c = a, ab, ca
        elif digit == "1":
            a, b, c = ab, b, bc
        elif digit == "2":
            a, b, c = ca, bc, c
        else:
            a, b, c = ab, bc, ca
    return a, b, c


def squared_distance(a, b):
    return sum((a[d]-b[d])**2 for d in range(3))


def verify_partition(paths, root_index):
    require(paths, f"root {root_index}: no witnesses")
    ordered = sorted(paths)
    for previous, current in zip(ordered, ordered[1:]):
        require(not current.startswith(previous),
                f"root {root_index}: duplicate or prefix-overlapping paths")
    # At the greatest finite depth L, a prefix-free path of length d covers
    # 4**(L-d) symbolic leaves. Equality to 4**L means all descendants exist;
    # closed midpoint cells then cover boundaries as well as interiors.
    require(sum((Fraction(1, 4**len(path)) for path in ordered), Fraction(0)) == 1,
            f"root {root_index}: incomplete subdivision partition")


def verify_direction(name, direction, patch, target, budget, declared_depth):
    require(type(direction) is dict, f"{name}: missing direction object")
    require(direction.get("certified") is True and direction.get("termination") == "certified",
            f"{name}: direction is not certified")
    require(direction.get("unresolved_frontier_cells_at_stop") == 0,
            f"{name}: unresolved cells")
    roots = root_representatives(patch)
    witnesses = direction.get("witnesses")
    require(type(witnesses) is list and len(witnesses) <= budget.max_witnesses,
            f"{name}: invalid witness list or witness budget exceeded")
    require(direction.get("input_source_faces") == len(patch), f"{name}: source-face count mismatch")
    require(direction.get("unique_source_geometries") == len(roots), f"{name}: root count mismatch")
    require(direction.get("input_target_faces") == len(target), f"{name}: target-face count mismatch")
    require(direction.get("unique_target_geometries") == len({geometry_key(t.points) for t in target}),
            f"{name}: unique target count mismatch")
    require(direction.get("certified_leaf_cells") == len(witnesses), f"{name}: leaf count mismatch")
    paths_by_root = {index: [] for index in roots}
    root_points = {index: exact_points(t) for index, t in roots.items()}
    target_points = {}
    identical_count = 0
    for number, witness in enumerate(witnesses):
        if number % 128 == 0:
            check_memory(budget)
        require(type(witness) is list and len(witness) in (4, 6), f"{name}: malformed witness {number}")
        root_index = strict_integer(witness[0], f"{name} root index")
        target_index = strict_integer(witness[2], f"{name} target index")
        require(root_index in roots, f"{name}: witness for omitted/nonrepresentative root {root_index}")
        require(target_index < len(target), f"{name}: target face index out of range")
        path = witness[1]
        require(type(path) is str and all(d in "0123" for d in path), f"{name}: invalid path")
        require(len(path) <= min(budget.max_depth, declared_depth), f"{name}: path exceeds depth budget")
        paths_by_root[root_index].append(path)
        if len(witness) == 4:
            require(witness[3] == "identical" and path == "", f"{name}: malformed identical witness")
            require(geometry_key(roots[root_index].points) == geometry_key(target[target_index].points),
                    f"{name}: false identical witness")
            identical_count += 1
            continue
        weights = [strict_integer(w, f"{name} barycentric weight") for w in witness[3:]]
        require(sum(weights) == DENOMINATOR, f"{name}: barycentric weights do not sum to denominator")
        cell = reconstruct_cell(root_points[root_index], path)
        center = tuple(sum(p[d] for p in cell)/3 for d in range(3))
        radius_squared = max(squared_distance(p, center) for p in cell)
        if target_index not in target_points:
            target_points[target_index] = exact_points(target[target_index])
        triangle = target_points[target_index]
        q = tuple(sum(weights[k]*triangle[k][d] for k in range(3))/DENOMINATOR for d in range(3))
        distance_squared = squared_distance(center, q)
        t = DELTA*DELTA-distance_squared-radius_squared
        require(t >= 0 and t*t >= 4*distance_squared*radius_squared,
                f"{name}: exact ball inequality failed at witness {number}, root {root_index}, path {path}")
    for root_index, paths in paths_by_root.items():
        verify_partition(paths, root_index)
    leaves = len(witnesses)
    internal_numerator = leaves-len(roots)
    require(internal_numerator >= 0 and internal_numerator % 3 == 0, f"{name}: invalid quadtree counts")
    internal = internal_numerator // 3
    depth = max((len(path) for paths in paths_by_root.values() for path in paths), default=0)
    require(direction.get("subdivisions") == internal, f"{name}: subdivision count mismatch")
    require(direction.get("visited_cells") == leaves+internal, f"{name}: visited count mismatch")
    require(direction.get("maximum_depth_seen") == depth, f"{name}: maximum depth mismatch")
    check_memory(budget)
    return {"verified": True, "root_geometries": len(roots), "witnesses_verified": leaves,
            "identical_witnesses": identical_count, "ball_witnesses": leaves-identical_count,
            "complete_partitions": len(roots), "maximum_depth": depth,
            "subdivision_nodes": internal, "no_target_search": True}


def verify_certificate(certificate_path, expected_witnesses=3303, budget=Budget(),
                       before_path=None, source_path=None, after_path=None):
    budget.validate()
    strict_integer(expected_witnesses, "expected witness count", 1)
    require(expected_witnesses <= budget.max_witnesses, "expected count exceeds verifier witness budget")
    certificate, certificate_sha = load_certificate(certificate_path, budget)
    require(certificate.get("schema") == "continuous-patch-coverage-v2", "unsupported schema")
    require(certificate.get("passed") is True and certificate.get("status") == "certified", "input is not a passed certificate")
    require(certificate.get("include_retained_background") is True, "full-surface background mode required")
    require(Fraction(certificate.get("delta_exact", "-1")) == DELTA and
            Fraction(certificate.get("delta_squared_exact", "-1")) == DELTA*DELTA,
            "exact delta must be 1/4, delta squared 1/16")
    proof = certificate.get("proof", {})
    require(type(proof) is dict and type(proof.get("barycentric_denominator")) is int and
            proof["barycentric_denominator"] == DENOMINATOR, "invalid barycentric denominator")
    declarations = certificate.get("budget_declared_before_geometry_checks", {})
    require(type(declarations) is dict, "missing producer budget declaration")
    declared_depth = strict_integer(declarations.get("max_depth"), "producer depth budget")
    require(declared_depth <= budget.max_depth, "producer depth exceeds verifier cap")
    directions = certificate.get("directions")
    require(type(directions) is dict and set(directions) == set(DIRECTION_NAMES), "wrong full-surface directions")
    total = 0
    for name in DIRECTION_NAMES:
        direction = directions[name]
        require(type(direction) is dict and type(direction.get("witnesses")) is list, f"{name}: missing witnesses")
        total += len(direction["witnesses"])
    require(total == expected_witnesses and total <= budget.max_witnesses,
            f"expected exactly {expected_witnesses} witnesses, found {total}")
    meshes, reports = {}, {}
    overrides = {"before": before_path, "source": source_path, "after": after_path}
    for name in ("source", "before", "after"):
        declared = certificate.get(name)
        require(type(declared) is dict and type(declared.get("path")) is str, f"missing {name} file declaration")
        path = overrides[name] if overrides[name] is not None else declared["path"]
        meshes[name], reports[name] = bounded_mesh(path, declared, budget)
    source_counts = Counter(oriented_key(t.points) for t in meshes["source"])
    patches = {name: source_subtraction(source_counts, meshes[name]) for name in ("before", "after")}
    for name in ("before", "after"):
        require(certificate.get(f"missing_or_reoriented_source_faces_{name}") == 0,
                f"declared {name} source loss")
        require(certificate.get(f"{name}_patch_faces") == len(patches[name]), f"{name}: patch count mismatch")
        require(certificate.get(f"{name}_patch_face_indices") == [t.face_index for t in patches[name]],
                f"{name}: patch extraction/index mismatch")
    results = {
        DIRECTION_NAMES[0]: verify_direction(DIRECTION_NAMES[0], directions[DIRECTION_NAMES[0]], patches["before"], meshes["after"], budget, declared_depth),
        DIRECTION_NAMES[1]: verify_direction(DIRECTION_NAMES[1], directions[DIRECTION_NAMES[1]], patches["after"], meshes["before"], budget, declared_depth)}
    check_memory(budget)
    return {"schema": "continuous-coverage-witness-replay-v1", "passed": True,
            "certificate": str(Path(certificate_path).resolve()), "certificate_sha256": certificate_sha,
            "meshes": reports, "delta_exact": "1/4", "hausdorff_upper_bound_exact": "1/4",
            "expected_witnesses": expected_witnesses, "witnesses_verified": total,
            "source_retained_in_both_with_multiplicity_and_orientation": True,
            "directions": results, "verifier_budget": budget.__dict__,
            "peak_process_rss_mib": peak_memory_mib(),
            "method": "exact leaf replay, complete prefix-free partitions, exact common-source retention; no nearest-point or target search",
            "shared_code": "strict VMESH wire reader only; no import from certify_patch_coverage.py",
            "limits": ["Only the identified stored binary32 triangle unions are certified.",
                       "Hausdorff as a set distance ignores duplicate multiplicity and orientation after retention is checked.",
                       "No equal-area, topology, intersection-free, anatomical or fibre-identity claim.",
                       "External project resource guard remains mandatory."]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--certificate", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expected-witnesses", type=int, default=3303)
    for name in ("before", "source", "after"):
        parser.add_argument("--"+name, type=Path)
    parser.add_argument("--max-witnesses", type=int, default=Budget.max_witnesses)
    parser.add_argument("--max-memory-mib", type=int, default=Budget.max_memory_mib)
    args = parser.parse_args(argv)
    if args.output.exists():
        print(f"Preserve existing output: {args.output}", file=sys.stderr)
        return 2
    try:
        budget = Budget(max_witnesses=args.max_witnesses, max_memory_mib=args.max_memory_mib)
        report = verify_certificate(args.certificate, args.expected_witnesses, budget,
                                    args.before, args.source, args.after)
    except (OSError, ValueError, TypeError, OverflowError, struct.error) as exc:
        report = {"schema": "continuous-coverage-witness-replay-v1", "passed": False,
                  "certificate": str(args.certificate), "reason": str(exc),
                  "note": "Verification failed closed; a resource/input failure is not a geometric counterexample."}
    try:
        with args.output.open("x") as stream:
            json.dump(report, stream, indent=2)
            stream.write("\n")
    except OSError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps({"passed": report["passed"], "witnesses_verified": report.get("witnesses_verified", 0),
                      "output": str(args.output), "reason": report.get("reason")}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
