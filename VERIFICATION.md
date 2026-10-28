# Standalone verification — October 28, 2026

## Result

Passed from a fresh project copy at `/tmp/vesuvius-surface-recovery-isolated-v1` using Python `-I -S`. The entire original lab directory, including ScrollFiesta source trees, old releases, libraries and binaries, was inaccessible inside the systemd service. The process explicitly checked that the lab root was unreadable before verification.

- Eight controls pass, covering live graph replay, alternative owners, retry, current constraints, incomplete/invalid evidence, exact shared-point contacts, geometric duplicates, whole-cycle fill, budget exhaustion, invalid cycles, obstructed-hole rejection, CLI isolation, I/O round trips and refusal to overwrite outputs.
- The standalone graft produces exactly the historical real graph's output labels and 27 recoveries.
- The independent hole stage retains all 5,143 indexed source faces and all vertex values, adds 17 faces and returns 5,160.
- Final exact new/source and new/new audit: 267 overlapping-AABB pairs, zero forbidden contacts.
- The oriented coordinate multiset equals historical v5. No claim of byte-identical file serialization across JSON and historical VMESH formats is made.
- Resource envelope: CPUQuota 25%, Nice 19, IOWeight 10, MemoryMax 384MiB, swap 0, GPU inaccessible, numerical thread limits 1, desktop reserve 3072MiB.
- Isolated run: about 13.8 seconds wall time; minimum available desktop memory about 6469MiB; peak child RSS about 42.25MiB.

Machine-readable results and the isolation command/log are in `verification/`. The self-contained source package contains no native executable or vendored dependency implementation. It runs without fetching any upstream repository or public CT array.

## Preserved development failures

The first fixture-export invocation and the original source package were not altered. The earlier upstream-review relative-path failure remains in its original record. In this standalone phase, the initial `-I -S` attempt failed to locate the packaged guard because isolated Python excludes the script directory. The tool now inserts its own tools directory explicitly; that failed log and the subsequent successful results are preserved. No failed result is reported as a passing test.

## Scientific limits

The graft result replays an exported graph from the historical experiment; the standalone tool does not independently regenerate the upstream projection/conflict graph from CT. The hole fixture is an already reconstructed source mesh and its cycle; the standalone tool independently recomputes the fill, not CT segmentation.

Exact contact checks concern added/source and added/added pairs. Unchanged source/source contacts are outside that certificate. The angle-fan interval test is necessary but does not provide a complete UV parameterization. There is no anatomical identity, minimum-clearance, fibers, complete CT-fidelity, full-scroll continuity or ink-reading certificate. These local fixture results do not establish universal superiority or worldwide novelty.

The old sealed archive is preserved unchanged as historical evidence. Independent execution does not erase upstream attribution or establish independent invention. The challenge form remains unsubmitted, and the repository is private by the user's request.
