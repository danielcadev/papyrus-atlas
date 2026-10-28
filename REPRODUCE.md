# Reproduction from a clean upstream tree

## Requirements and scope

Linux with cgroup v2, a working user systemd manager, GCC/G++, CMake 3.24+, Ninja, GNU patch, Python 3 and NumPy. A libtiff runtime is required; the checked recipe configures the pinned upstream's vendored TIFF headers. Install your distribution's development package if appropriate, or pass `--tiff-library /absolute/path/to/libtiff.so`. The exact checked environment, compiler flags and versions are recorded with the verification results. The experiment does not require a GPU or an AI service/API.

The main Python requirement is NumPy (`numpy>=1.24,<3`; tested version is recorded). Matplotlib is optional for regenerating the illustration. No Python dependencies, compiler or upstream executable are bundled. Do not install them into a globally managed environment without following your system's normal package policy.

The wrapper enforces CPUQuota 25%, Nice 19, IOWeight 10, MemoryMax 384 MiB, MemorySwapMax 0, inaccessible GPU devices, five numerical thread limits of one and at least 3,072 MiB desktop reserve. Every computational command below goes through it. Commands stop rather than relax those requirements. Run sequentially, use fresh names/paths and retain failed outputs.

## Commands

Extract the release, enter its top-level directory, then set absolute paths:

```bash
PKG=$(pwd)
REPRO_TAG=$(date -u +%Y%m%dT%H%M%SZ)
RUN_ROOT="$HOME/vesuvius-replay-$REPRO_TAG"
export VES_RELEASE_LOG_DIR="$RUN_ROOT/logs"
```

Verify the release's files:

```bash
bash "$PKG/tools/run_guarded.sh" "verify-$REPRO_TAG" 120 \
  python3 "$PKG/tools/verify_release.py"
```

Download the pinned public upstream and apply all four dependency-ordered patches. No Git working tree, precompiled laboratory library or local research folder is needed:

```bash
bash "$PKG/tools/run_guarded.sh" "bootstrap-$REPRO_TAG" 180 \
  python3 "$PKG/tools/bootstrap.py" --destination "$RUN_ROOT/upstream"
```

An already downloaded original archive can be supplied with `--archive /absolute/path/source.tar.gz`; its digest is still mandatory. The expected upstream archive is 77,065,617 bytes, SHA256 `8d274779c379dd3146dccb6c6be746b59a0261a2836036f16f66f965d23b6e29`.

Build and reproduce the real-data result:

```bash
bash "$PKG/tools/run_guarded.sh" "reproduce-$REPRO_TAG" 1800 \
  python3 "$PKG/tools/reproduce.py" \
  --source "$RUN_ROOT/upstream/source" --work "$RUN_ROOT/reproduction"
```

This downloads the original CT when `--volume` is omitted. A local copy can be passed with `--volume /absolute/path/01744_02256_04048_volume.nrrd`; the original byte digest is still checked. To retrieve both CT and post-hoc reference labels separately:

```bash
bash "$PKG/tools/run_guarded.sh" "data-$REPRO_TAG" 180 \
  python3 "$PKG/tools/fetch_inputs.py" --output "$RUN_ROOT/public-data"
```

## What constitutes a pass

`reproduction/verification.json` must contain `passed: true`. The recipe:

1. Verifies the patch series, exact source files, reference meshes and control fixture.
2. Builds `cube_mesh` and its dependencies from clean source, with `--parallel 1`, C/C++ Release `-O2 -DNDEBUG`. It independently builds/runs the actual production graft helper's positive and negative controls with assertions enabled.
3. Reconstructs the original Otsu input from the public CT, verifying raw prediction bytes before native execution.
4. Runs full v4-control and v5-recovery pipelines on identical input. Both must retain the same 5,139-face source. Their final 5,143/5,160-face geometry must equal the corresponding preserved geometry exactly, modulo oriented face order.
5. Recomputes the independent rational intersection certificate for all new/v4-source and new/new overlapping-AABB pairs: 17 new faces, 267 exact pairs, zero forbidden contacts. It does not claim an exact source/source or anatomical certificate.
6. Changes only the graft implementation to its pre-graft fixture, recompiles incrementally, runs the full control pipeline and verifies that all pre-graft source faces are retained with exactly 27 additions in the grafted source. It restores the v5 source and executable afterward.

Historical coverage, probe-distance and native-audit metrics are reused only after exact oriented geometry equality. This avoids pretending to add independent anatomical validation or rerunning unchanged measurements. Their original inputs, recorded commands, outputs and scope are exported under `evidence/`.

The checked full reproduction used cached byte-identical upstream/CT inputs; separate online-download checks are recorded in `verification/`. Final tooling adds reference/fixture digest checks; `verification/executed-reproduce-01.py` preserves the benchmark-executed recipe and the additional digest checks have their own receipt. These checks do not change geometry or acceptance thresholds.

## Interpreting evidence and failures

`evidence-index.json` distinguishes exported files, external inputs/executables, and historical references whose current contents differ from an earlier manifest. One historical CONTEXT.md reference changed as the working notebook evolved; no claim is made that its current copy matches that older digest. Frozen production-v5 sources, meshes and successful certificates remain distinct and checked.

Historical scripts may contain original absolute paths and Spanish prose; they are provenance records, not the portable entry point. Use `tools/bootstrap.py` and `tools/reproduce.py` above. New release documentation is in English. No file is overwritten in a historical result folder.

If the guard stops a run or any digest, geometry, contact, topology or count assertion fails, preserve `verification-failed.json`, logs and outputs. Do not force a pass, remove source faces, alter input predictions or relax limits. A timeout is an incomplete experiment, not evidence that recovery is impossible.
