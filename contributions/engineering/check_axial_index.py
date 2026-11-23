"""Verify planar distance decisions against a full KD tree on a saved CT-derived mesh."""
import argparse
from pathlib import Path
from time import perf_counter

import numpy as np
from scipy.spatial import cKDTree

from axial_index import axial_index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args()
    with np.load(args.fixture, allow_pickle=False) as fixture:
        vertices, plane, queries = (fixture[k] for k in ("vertices_zyx", "plane_z", "queries_zyx"))
    assert np.all(queries[:, 0] == plane)
    start = perf_counter()
    expected = cKDTree(vertices).query(queries)[0]
    baseline = perf_counter() - start
    start = perf_counter()
    tree, lower_bound, kept, omitted = axial_index(vertices, float(plane))
    result = np.full(len(queries), lower_bound)
    if tree is not None:
        result = np.minimum(result, tree.query(queries)[0])
    elapsed = perf_counter() - start
    assert np.array_equal(expected > 16, result > 16)
    assert np.any(expected <= 16) and np.any(expected > 16)
    assert np.all(result <= expected + 1e-12)
    print(f"{len(queries):,} decisions exact; {kept:,} vertices indexed, {omitted:,} omitted")
    print(f"Local KD-tree construct/query comparison {baseline:.6f} s → {elapsed:.6f} s")


if __name__ == "__main__":
    main()
