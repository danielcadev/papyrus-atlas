"""Reconnect a complete fixed-UV contact cover without changing the UV map."""
import argparse
import heapq
import json
from pathlib import Path

import numpy as np
from scipy.ndimage import label
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra


def component_areas(keep, mapped, shape, areas):
    lattice = np.zeros(shape, dtype=bool)
    lattice.ravel()[mapped[keep]] = True
    labels, count = label(lattice)
    components = labels.ravel()[mapped]
    mass = np.bincount(components, weights=areas, minlength=count + 1)
    return components, mass[1:]


def cover_conflicts(mandatory, conflicts, areas, protected):
    """Greedy area-weighted cover. Rail cells lose conflicts after other cells."""
    blocked = mandatory.copy()
    neighbors = {}
    for a, b in conflicts[~blocked[conflicts].any(axis=1)]:
        neighbors.setdefault(int(a), set()).add(int(b))
        neighbors.setdefault(int(b), set()).add(int(a))
    heap = []

    def offer(cell):
        degree = len(neighbors[cell])
        if degree:
            heapq.heappush(heap, (bool(protected[cell]), areas[cell] / degree, cell, degree))

    for cell in neighbors:
        offer(cell)
    while heap:
        _, _, cell, degree = heapq.heappop(heap)
        if blocked[cell] or len(neighbors[cell]) != degree:
            continue
        blocked[cell] = True
        for other in neighbors[cell]:
            neighbors[other].remove(cell)
            offer(other)
        neighbors[cell].clear()
    if not blocked[conflicts].any(axis=1).all():
        raise RuntimeError("Failed to cover all input conflicts.")
    return blocked


def reconnect(mapped, shape, areas, mandatory, conflicts, rail):
    size = len(mapped)
    if mapped.min() < 0 or mapped.max() >= np.prod(shape) or len(np.unique(mapped)) != size:
        raise ValueError("Grid positions must be distinct and in bounds.")
    if not np.all(np.isfinite(areas) & (areas > 0)) or len(areas) != size:
        raise ValueError("Provide one positive finite native area per cell.")
    if len(mandatory) != size or np.any((conflicts < 0) | (conflicts >= size)):
        raise ValueError("Invalid mandatory veto array or conflict indices.")
    if not len(rail) or np.any((rail < 0) | (rail >= size)) or mandatory[rail].any():
        raise ValueError("The supplied certified rail must be in bounds and free of hard vetoes.")

    protected = np.zeros(size, dtype=bool)
    protected[rail] = True
    blocked = cover_conflicts(mandatory, conflicts, areas, protected)
    if blocked[rail].any():
        raise ValueError("The baseline cover could not preserve the complete certified rail.")
    components, mass = component_areas(~blocked, mapped, shape, areas)
    baseline_tag = int(mass.argmax()) + 1
    baseline = components == baseline_tag
    report = {
        "baseline_largest_area": float(areas[baseline].sum()),
        "baseline_total_area": float(areas[~blocked].sum()),
        "bridge_accepted": False,
    }
    if len(mass) < 2:
        return baseline, baseline, report

    source_tag, target_tag = np.argsort(mass)[-2:][::-1] + 1
    rivals = np.concatenate((conflicts, conflicts[:, ::-1]))
    forbidden = mandatory.copy()
    forbidden[rivals[protected[rivals[:, 1]], 0]] = True
    loss = np.bincount(rivals[:, 0], weights=areas[rivals[:, 1]] * (~blocked[rivals[:, 1]]), minlength=size)
    grid = np.full(shape, -1, dtype=np.int32)
    grid.ravel()[mapped[~forbidden]] = np.flatnonzero(~forbidden)
    pairs = np.concatenate((
        np.stack((grid[:-1].ravel(), grid[1:].ravel()), axis=1),
        np.stack((grid[:, :-1].ravel(), grid[:, 1:].ravel()), axis=1),
    ))
    edges = pairs[(pairs >= 0).all(axis=1)]
    edges = np.concatenate((edges, edges[:, ::-1]))
    starts = np.unique(edges[(components[edges[:, 0]] == source_tag) &
                             (components[edges[:, 1]] != source_tag), 0])
    if not len(starts):
        return baseline, baseline, report

    weight = 1e-6 + blocked * (areas + loss)
    graph = csr_matrix((weight[edges[:, 1]], edges.T), shape=(size, size))
    distance, previous, _ = dijkstra(graph, indices=starts, min_only=True, return_predecessors=True)
    ends = np.flatnonzero(components == target_tag)
    end = ends[np.argmin(distance[ends])]
    if not np.isfinite(distance[end]):
        return baseline, baseline, report

    path = np.zeros(size, dtype=bool)
    while end >= 0:
        path[end] = True
        end = previous[end]
    restored = path & blocked
    veto = rivals[restored[rivals[:, 0]], 1]
    if path[veto].any():
        return baseline, baseline, report
    trial = blocked & ~path
    trial[veto] = True
    if not trial[mandatory].all() or not trial[conflicts].any(axis=1).all():
        raise RuntimeError("The trial does not satisfy all input vetoes.")
    changed, changed_mass = component_areas(~trial, mapped, shape, areas)
    route_labels = np.unique(changed[rail])
    if len(route_labels) != 1 or route_labels[0] == 0:
        return baseline, baseline, report
    tag = route_labels[0]
    if changed_mass[tag - 1] <= report["baseline_largest_area"]:
        return baseline, baseline, report
    result = changed == tag
    report.update(bridge_accepted=True, path_cells=int(path.sum()),
                  restored_cells=int(restored.sum()), removed_conflicting_cells=int((trial & ~blocked).sum()),
                  selected_area=float(areas[result].sum()), selected_cells=int(result.sum()))
    return baseline, result, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path, help="New output directory")
    args = parser.parse_args()
    with np.load(args.input, allow_pickle=False) as fixture:
        baseline, selected, report = reconnect(*(fixture[k] for k in (
            "mapped", "shape", "area_native_voxels2", "mandatory", "conflicts", "rail_cells"
        )))
        ids = fixture["source_cell_ids"]
        pitch = float(fixture["pitch_mm"])
        xyz, faces, face_ids, uv = (fixture[k] for k in ("native_zyx", "faces", "source_face_ids", "uv"))
    keep_faces = np.r_[selected, selected]
    used, inverse = np.unique(faces[keep_faces], return_inverse=True)
    for name in ("baseline_largest_area", "baseline_total_area", "selected_area"):
        if name in report:
            report[f"{name}_mm2"] = report.pop(name) * pitch**2
    args.output.mkdir()
    np.savez_compressed(args.output / "selection.npz", baseline_cell_ids=ids[baseline],
                        selected_cell_ids=ids[selected])
    np.savez_compressed(args.output / "chart.npz", native_zyx=xyz[used],
                        faces=inverse.reshape(-1, 3).astype(np.int32),
                        source_face_ids=face_ids[keep_faces], uv=uv[used])
    (args.output / "metrics.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
