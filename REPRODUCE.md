# Reproduce without ScrollFiesta

Requirements: Python 3.10+ standard library, Bash and a Linux user systemd session for the lab resource wrapper. There is no compiler, package installer, network fetch or external source checkout in this workflow. CLI/library operation itself is portable Python; the guard intentionally targets Linux.

From this directory, use an absolute output directory that does not yet exist:

```bash
bash tools/run_guarded.sh standalone-verify-UNIQUE 180 python3 -I -S "$PWD/tools/verify_project.py" /tmp/vesuvius-standalone-verification-UNIQUE
```

The verification tool inserts only this project into Python's path. `-I -S` disables environment-driven Python imports and site packages. The wrapper preserves CPUQuota=25%, Nice=19, IOWeight=10, MemoryMax=384MiB, MemorySwapMax=0, inaccessible GPU paths, five numerical thread limits of one and at least 3072MiB available desktop RAM. It never closes applications.

The test run checks fixture hashes, independent controls, 27 graft-graph recoveries, the real 19-cycle recovery, full source-index and coordinate preservation, a final exact audit of all added/source and added/added overlapping pairs, and oriented geometry equality against the historical v5 reference. Generated reports and meshes are saved to the new output directory. A refusal produces an explicit report, not a partial mesh fill.

For the CLI under the same resource envelope:

```bash
bash tools/run_guarded.sh standalone-graft-UNIQUE 60 python3 -I -S "$PWD/tools/run_cli.py" graft "$PWD/tests/fixtures/graft-input.json" /tmp/graft-UNIQUE.json
bash tools/run_guarded.sh standalone-hole-UNIQUE 180 python3 -I -S "$PWD/tools/run_cli.py" recover "$PWD/tests/fixtures/paris4-source.json" "$PWD/tests/fixtures/paris4-cycle.json" /tmp/recovered-UNIQUE.obj --report /tmp/recovery-UNIQUE.json
```

The graph API requires complete source-edge/conflict constraints. It cannot infer their completeness. Hole recovery is capped at 19 cycle vertices, 2,000,000 search nodes and 20,000,000 pair queries. Optional API budgets may reduce, but cannot increase, those ceilings. Scratch admission uses a conservative input-size bound within a 128MiB planning allowance; the operating-system memory guard is the hard enforcement layer. This is not a universal Python heap-size proof.

Fixture origin and exact hashes are in PROVENANCE.json. Using a historical mesh as input does not require its original producer; no claim of an independent CT-to-mesh reconstruction is made.
