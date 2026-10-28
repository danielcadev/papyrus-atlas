# Attribution and independent execution

Vesuvius Surface Recovery is maintained as an independent Vesuvius Lab mesh-processing project. Its Python package has no runtime or build dependency on ScrollFiesta or its third-party dependency tree.

The boundary-graft design, complete-cycle interval search, source-preservation rules and angle-fan condition descend from the lab's experimental modifications to public ScrollFiesta at revision `bce8a65f97652316efb084171a17d2f1f8d3ae1a`. The angle-bound formulas and boundary-oriented design were informed by that implementation. These are attributed derivative ideas/implementation patterns, not a claim of clean-room invention. Ben Kyles's ScrollFiesta MIT notice is preserved in LICENSES/ScrollFiesta-MIT.txt, and the project license retains both upstream and contributed-work attribution.

The exact rational triangle-contact module is reused from the lab's independent, standard-library-only auditor preserved in the earlier package. It loads no native geometric predicates. The original source digest is recorded in PROVENANCE.json.

Historical graph input was exported from the actual graft call during a separately saved instrumented Paris4 pipeline run. The export instrumentation and its logs remain in the lab's `research/independent-fixture-export-v1/` and `research/native/`. The new graph implementation receives only labels, original-edge adjacency, conflict pairs and the completeness flag; expected output labels are isolated in a test reference file. The historical producer is provenance for this fixture, not a dependency of the new tool.

The Paris4 mesh fixtures retain public PHercParis4 / Scroll 1 CT provenance, cube `01744_02256_04048`. Their source is the earlier Otsu +32Y experiment; original CT/annotations remain separately attributed and are not relicensed. The input cycle is selected from the conservative source mesh alone as its only isolated length-19 boundary; expected historical output triangles are used only for post-hoc comparison.

No Triangle, GCO, Clipper2, andres/graph implementation or compiled executable is included in the standalone runtime. Historical upstream notices remain relevant to the separate legacy archive and are not replaced by the standalone project's license.

Codex AI assistants helped implement, debug, review and document this project. This does not establish worldwide novelty, an AI-laboratory discovery, anatomical correctness or new text.
