# Vesuvius Surface Recovery

An independent mesh-stage research project with two deterministic surface recovery methods. **Execution requires Python 3.10+ and its standard library only.** No ScrollFiesta checkout, native library, compiler, NumPy, Triangle, Clipper2, GCO, trained model, API, network access or GPU is required.

The project has its own importable package and command-line interface. It accepts triangular meshes in JSON and plain Wavefront OBJ; a strict import-only adapter supports historical VESMESH1 fixtures. It refuses UV-bearing historical files rather than silently dropping their UV coordinates.

## Methods

- **Boundary grafting:** compatible original faces attach to retained owners through original shared-edge adjacency. Retained owners do not merge or move. Complete conflict constraints are an explicit input, not an assumed geometry certificate. Final assignments are committed atomically after all recorded constraints pass.
- **Whole-cycle hole recovery:** a bounded search triangulates an isolated 3–19 vertex source boundary without moving vertices, welding, discarding source triangles or adding Steiner vertices. New/source and new/new contacts are checked with exact rational arithmetic, including shared-point cases. Source diagonals, boundary orientation, degeneracy, shape and necessary angle-fan bounds remain admission controls. Failure or exhaustion commits no patch.

This independent Python implementation descends from experiments on public ScrollFiesta. Runtime independence does **not** mean independent historical origin or worldwide novelty. Attribution and MIT notices remain in ATTRIBUTION.md and LICENSES/. Historical results and their original interpretation remain preserved separately.

## Run

There is no installation or build step. From this project directory:

```bash
python3 -m vesuvius_surface --help
python3 -m vesuvius_surface graft tests/fixtures/graft-input.json /tmp/graft-result.json
python3 -m vesuvius_surface recover tests/fixtures/paris4-source.json tests/fixtures/paris4-cycle.json /tmp/recovered.obj --report /tmp/recovery-report.json
```

Use unique output filenames: existing results are never overwritten. The API is `Mesh`, `boundary_graft` and `recover_cycle`; see the modules and tests for examples. For experiments in the lab, use the unchanged resource guard as shown in REPRODUCE.md instead of launching unrestricted computation.

## Verified scope

The exported historical real-data graft graph reproduces all 27 assignments exactly. The independent hole stage fills the Paris4 cycle with 17 faces, retaining 5,143 source faces and reaching 5,160. Its oriented geometry matches the historical v5 output, with zero forbidden contacts in the 267 final overlapping-AABB new-face pairs. See VERIFICATION.md for the exact run and limitations.

The supplied graph and mesh fixtures originate from public PHercParis4 / Scroll 1 data processed during earlier experiments. This is a standalone **mesh-processing project**, not a standalone CT-to-text system: it does not extract or segment CT, infer fibers, flatten meshes or detect ink. Its graft API consumes supplied complete adjacency/conflict evidence; it does not yet generate that evidence from CT or detect arbitrary projected chart conflicts. The exact checker does not recertify unchanged source/source pairs. Angle bounds are necessary conditions, not a full UV certificate. No anatomical identity, new letters, whole-scroll continuity, current-upstream superiority or prize is claimed.

## Historical evidence

The original sealed software package, archive checksum, upstream-derived snapshots, failures and comparisons are retained unchanged in the lab and in the private legacy release. PROVENANCE.json records source and fixture hashes. The standalone project does not load that archive. The private repository has not been submitted to the challenge; the old public contribution URL is no longer publicly accessible.
