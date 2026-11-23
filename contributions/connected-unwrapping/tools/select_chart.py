"""Rebuild a bounded connected chart from exact, single-valued native cells."""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.ndimage import label
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra


def select_chart(vertices, quads, cell_ids, baseline_ids, veto_ids, pitch_mm, max_faces):
    projections = vertices[quads, :2]
    origin = projections[:, 0].min(axis=0)
    sites = (projections[:, 0] - origin).astype(np.int64)
    offsets = np.array([[0, 0], [1, 0], [0, 1], [1, 1]])
    if not np.array_equal(projections - origin, sites[:, None] + offsets):
        raise ValueError("Each quad must occupy one complete unit cell in the native Z/Y plane.")
    grid = np.full(tuple(sites.max(axis=0) + 1), -1, dtype=np.int32)
    key = tuple(sites.T)
    grid[key] = np.arange(len(quads))
    if np.count_nonzero(grid >= 0) != len(quads):
        raise ValueError("Multiple sheets occupy the same projected cell.")
    if not np.array_equal(np.unique(cell_ids), cell_ids):
        raise ValueError("Source cell IDs must be unique and sorted.")
    if not (np.isin(baseline_ids, cell_ids).all() and np.isin(veto_ids, baseline_ids).all()):
        raise ValueError("The baseline and veto sets must belong to the original support.")

    # Check native edge agreement as well as adjacent projected coordinates.
    edges = []
    for first, second, first_side, second_side in (
        (grid[:-1], grid[1:], (1, 3), (0, 2)),
        (grid[:, :-1], grid[:, 1:], (2, 3), (0, 1)),
    ):
        adjacent = (first >= 0) & (second >= 0)
        a, b = first[adjacent], second[adjacent]
        if not np.array_equal(quads[a][:, first_side], quads[b][:, second_side]):
            raise ValueError("Adjacent projected cells disagree on a native edge.")
        edges.append((a, b))

    a, b, c, d = vertices[quads, 2].T
    areas = 0.5 * pitch_mm**2 * (
        np.sqrt(1 + (a - b)**2 + (d - b)**2)
        + np.sqrt(1 + (a - c)**2 + (d - c)**2)
    )
    veto = np.isin(cell_ids, veto_ids)
    baseline = np.isin(cell_ids, baseline_ids)
    image = np.zeros(grid.shape, dtype=bool)
    image[key] = baseline & ~veto
    components, count = label(image)
    classes = components[key]
    sizes = np.bincount(classes, weights=np.where(classes > 0, areas, 0), minlength=count+1)
    if not count:
        raise ValueError("No baseline component survives the vetoes.")
    seed = classes == sizes.argmax()

    u, v = (np.concatenate([edge[i] for edge in edges]) for i in range(2))
    valid = ~(veto[u] | veto[v])
    u, v = u[valid], v[valid]
    graph = coo_matrix(
        (np.ones(2*len(u), dtype=np.uint8), (np.r_[u, v], np.r_[v, u])),
        shape=(len(quads), len(quads)),
    ).tocsr()
    distance = dijkstra(graph, indices=np.flatnonzero(seed), min_only=True, unweighted=True)
    budget = max_faces // 2
    if np.count_nonzero(seed) > budget:
        raise ValueError("The starting component exceeds the face budget.")
    # Exclude the entire tied distance layer when it would exceed the budget.
    limit = np.partition(distance, budget)[budget] if budget < len(distance) else np.inf
    keep = distance < limit
    if not keep[seed].all():
        raise ValueError("The budget cannot retain the starting component under the tied-layer rule.")
    image[key] = keep
    if label(image)[1] != 1:
        raise RuntimeError("Selected chart is disconnected.")
    report = {
        "maximum_faces": max_faces,
        "baseline_cells": int(baseline.sum()),
        "baseline_largest_after_veto_mm2": float(areas[seed].sum()),
        "mandatory_veto_cells": int(veto.sum()),
        "selected_cells": int(keep.sum()),
        "selected_area_mm2_before_refit": float(areas[keep].sum()),
        "selected_outside_baseline_mm2": float(areas[keep & ~baseline].sum()),
    }
    return keep, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path, help="New output directory")
    parser.add_argument("--max-faces", type=int, default=2_500_000)
    args = parser.parse_args()
    with np.load(args.input, allow_pickle=False) as fixture:
        xyz, quads, ids, baseline, veto = (
            fixture[k] for k in ("native_zyx", "quads", "source_quad_ids", "baseline_ids", "veto_ids")
        )
        keep, metrics = select_chart(xyz, quads, ids, baseline, veto, float(fixture["pitch_mm"]), args.max_faces)
    args.output.mkdir()
    used, index = np.unique(quads[keep], return_inverse=True)
    np.savez_compressed(args.output / "chart.npz", native_zyx=xyz[used],
                        quads=index.reshape(-1, 4), source_quad_ids=ids[keep])
    (args.output / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
