# Reject a coincident triangle pair in a chart-cycle fill

ScrollFiesta base `3c46077968c0151dd185656c16d5063cdbb3f5aa`. The included diff changes one C source. The before/after comparison uses the same saved pre-fill mesh and upstream `HoleFill_process_ex` in chart mode.

On a CT-derived PHercParis4 fixture, the baseline produces 5,160 faces with one nondegenerate exact duplicate group. The patch leaves the problematic cycle open, accepts a separate valid fill and emits 5,143 faces with zero duplicate groups. All 5,139 oriented source faces are retained exactly. A separate control mesh is byte-identical across builds. See [comparison.json](comparison.json).

## Reproduction on Linux

Clone the public ScrollFiesta repository and check out the pinned commit in a fresh worktree. Keep this package outside the worktree and set `package` to its absolute path. Configure the public full CMake profile with TIFF development headers and Ninja.

```bash
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DSCROLLFIESTA_BUILD_TOOLS=ON -DSCROLLFIESTA_BUILD_TESTS=ON -DSCROLLFIESTA_WITH_TIFF=ON
cmake --build build --parallel 4
cc -O2 -std=gnu17 -I src -I deps/include -c "$package/replay_holefill.c" -o replay.o
link_replay() {
  c++ -fopenmp replay.o build/libscrollfiesta_core.a build/libsf_triangle.a \
    build/clipper2/libClipper2.a -ltiff -lm -o "$1"
}
link_replay replay-before
./replay-before "$package/fixtures/problem.vmesh" problem-before.vmesh
./replay-before "$package/fixtures/control.vmesh" control-before.vmesh
git apply "$package/scrollfiesta-holefill.patch"
cmake --build build --parallel 4
link_replay replay-after
./replay-after "$package/fixtures/problem.vmesh" problem-after.vmesh
./replay-after "$package/fixtures/control.vmesh" control-after.vmesh
cmp control-before.vmesh control-after.vmesh
python "$package/exact_mesh_certificate.py" --before problem-before.vmesh \
  --after problem-after.vmesh --source "$package/fixtures/problem.vmesh" --output certificate.json
ctest --test-dir build --output-on-failure
```

The fixtures are derived from the Vesuvius Challenge PHercParis4 CT used for the lab's ScrollFiesta comparison. The fixture evidence retains its source data terms and attribution. See [Vesuvius Challenge data](https://scrollprize.org/data) and the [PHercParis4 data record](https://scrollprize.org/data_browser/PHercParis4). The code and upstream patch retain their MIT notices.

The checked run used GNU 16.2.1 on Linux x86-64. All 25 tests passed, including the native hole-fill and cube-mesh self-tests. See [ctest.log](ctest.log). Our lab supplied its previously cached TIFF development headers and the installed system TIFF library explicitly to CMake.

The complete example archives, reproducible fixtures and checksums are available from the [November 2026 release](https://github.com/danielcadev/papyrus-atlas/releases/tag/progress-prize-2026-11).
