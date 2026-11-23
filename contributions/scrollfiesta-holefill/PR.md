# holefill: reject coincident triangles in chart-cycle fills

## Summary

A chart-cycle fill can satisfy the indexed boundary certificate while emitting two geometrically identical triangles with opposite winding. This occurs when distinct boundary IDs occupy the same three-dimensional position. The change detects exact coordinate duplicates inside a proposed chart-cycle fill and discards that proposal before stitching. Other holes can still be filled. Existing source vertices and faces remain untouched.

## Validation

- [x] Built every changed source file with a documented profile
- [x] Ran the relevant CTest suite
- [x] Ran applicable self-tests
- [x] Compared representative before/after metrics or audits
- [ ] Ran an install smoke test (packaging or CMake changes)

On Linux x86-64 with GCC 16.2.1, the full TIFF-enabled CMake profile built at `3c46077968c0` with and without the change. The attached PHercParis4 pre-fill fixture was replayed through `HoleFill_process_ex` in chart mode. Baseline: 5,160 faces and one exact nondegenerate duplicate group. Patched: 5,143 faces and zero duplicate groups, with all 5,139 original oriented faces preserved. The independent unaffected fixture produced byte-identical meshes. CTest passed all 25 tests, including cube_mesh_selftest and holefill_interior_test. The install smoke test is outside this source-only change.

## Integration impact

- [x] No public API or ABI change
- [x] No canonical artifact update
- [x] No dependency or licensing change
- [x] Documentation matches changed commands, defaults and outputs

The proposed commit changes only `src/holefill/hole_fill.c`. The small regression evidence and commands can be uploaded as a separate attachment. Codex assisted with implementation, reproduction and the write-up.
