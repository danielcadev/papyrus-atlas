# Attribution, licenses and AI assistance

## Software

This independent experimental contribution modifies [ScrollFiesta public](https://github.com/Hob3rMallow/scrollfiesta_public), revision `bce8a65f97652316efb084171a17d2f1f8d3ae1a`, copyright 2026 Ben Kyles. Its MIT notice is retained in `LICENSES/ScrollFiesta-MIT.txt`. Patches, control fixtures and historical source snapshots include ScrollFiesta code; they are not wholly original replacements for its pipeline. The newly contributed release tooling and modifications are provided under the accompanying MIT license.

The complete upstream checkout and third-party dependency sources or executables are **not** bundled. Bootstrap retrieves the original pinned archive directly and verifies its SHA256. The upstream checkout contains dependencies with separate terms, including GCoptimization, Triangle, Clipper2, attene-predicates and andres/graph. Consult its `THIRD_PARTY_LICENSES.md`, `docs/research/gco-v3.0/GCO_README.TXT` and `deps/src/triangle/README` before using or redistributing a locally built executable. This release does not relicense those dependencies or claim that the complete dependency tree is MIT.

In particular, GCoptimization specifies research-use and redistribution conditions; its documentation requests citations to Boykov, Veksler and Zabih (2001), Kolmogorov and Zabih (2004), and Boykov and Kolmogorov (2004), with additional attribution if label costs are used. Triangle has its own redistribution notice and commercial-distribution conditions. The vendored andres/graph license provenance is not resolved by this package. No corresponding implementation or compiled binary is exported here. These are upstream dependency disclosures, not a claim of new rights or permissions.

## Data and scientific attribution

The principal reproducibility case uses public PHercParis4 (Scroll 1) CT cube `01744_02256_04048` from the Vesuvius Challenge harmonized manual-instance-label collection. `public-data.json` records original URLs, lengths and hashes for CT and annotations. Original arrays are downloaded directly, not redistributed or relicensed here. Derived meshes, recorded metrics and historical illustrations retain that data provenance and are not covered by an assertion of exclusive ownership. See the Vesuvius Challenge data providers' terms for underlying data use and attribution.

The +32Y surface prediction is classical Otsu thresholding, threshold 134, within a predeclared 32³ window, zero elsewhere. Manual instance labels are used for post-hoc evaluation, not this input prediction. Sampled windows from the same cube/scroll do not establish generalization to other scrolls.

## What AI did and did not contribute

Codex assistants helped with source inspection, algorithm implementation, debugging, experimental orchestration, critical reviews and documentation. Historical records identify Sol/Astra assistance where used. Assistance and model names are not a published algorithm or evidence of correctness. Claims here are supported by saved inputs, output geometry, controls and independent checks.

The two submitted improvements are deterministic computational geometry: compatible source-face attachment on original edges and bounded complete-cycle triangulation with atomic rejection. No new AI-laboratory discovery, new neural model, model training, hidden research access, new ancient-text reading or worldwide novelty is claimed. ScrollFiesta's broader ecosystem can consume learned surface predictions; that does not mean such a model was trained or evaluated in this Otsu experiment.
