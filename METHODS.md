# Methods and integration

## Pinned experimental baseline

The series in `patches/series.json` is applied in order to public ScrollFiesta revision `bce8a65f97652316efb084171a17d2f1f8d3ae1a`. Every changed file has before/after digests; the complete expected final source set is checked before compilation. The baseline patch contains previously developed soft MLS-edge adaptation, coverage-aware split handling and recorded pipeline/halo support needed to reproduce the experimental setup. These dependencies are disclosed rather than attributed to either of the two new stages. Later PHerc0813/v6 exact-contact modifications are excluded.

## Boundary Grafting v2

The source triangles already exist before component filtering. A coverage veto alone did not preserve all useful triangles when a later minimum-component-size rule discarded their small owners. Attaching the whole component could admit triangles incompatible with retained neighbors.

The graft operates on the original-edge graph. It considers individual triangles of small components for attachment to retained neighboring owners, including retained owners other than the largest. It ranks possible owners deterministically by shared-edge count, then ID. Recorded incompatibilities are checked against current assignments, so conflicts with faces recovered earlier in the same pass still reject an attachment. A previously blocked face can be retried if another neighbor supplies a newly available owner.

The stage does not move vertices, invent triangles, merge owners or turn off the minimum-component rule for residual fragments. Labels are written only after all recorded pair constraints are validated. Incomplete conflict-pair collection disables the new recovery. This is deliberately fail-closed, but the native overlap detector's shared-point blind spots remain a limitation rather than a general intersection proof.

The experiment is enabled by `VES_OVERLAP_COVERAGE_GUARD=1`. The pre-graft control in this release retains that baseline flag and changes only the graft implementation, preserving the distinction between the earlier coverage protection and the new recovery. The production-helper control covers alternative owners, blocked faces, chains, conflicts with already recovered faces, retry, determinism, invalid input and saturated detection.

## Duplicate correction and Hole Recovery v5

The reproduced failure emitted the same geometric triangle twice, with opposite orientations and potentially different vertex IDs. The v4 correction detects geometric equality and rejects the invalid greedy proposal; this preserves source but leaves the target cycle open.

The opt-in v5 path searches complete triangulations of that same cycle after the greedy duplicate-producing proposal is rejected. Its domain is cycles of 3–19 vertices, at most 969 candidate triples. Limits include 2,000,000 search nodes, 20,000,000 pair-predicate calls during preprocessing, a 128 MiB allocation ceiling and depth at most 17. Exhaustion, invalid inputs or failure rejects the whole proposal; no partial fill is committed.

Candidates reuse cycle IDs and coordinates, with exactly n−2 faces and no Steiner vertices. Existing source triangles and valid earlier fills remain unchanged. Boundary degree/orientation, valid metric, geometric duplicate exclusion, forbidden source diagonals, shape, angular-fan and intersection filters remain active. Candidate/source, candidate/previous-fill and internal compatibility checks are not substituted for an anatomical certificate. A prior fill with unresolved merges prevents this path from proceeding.

`VES_HOLE_RECOVERY_SEARCH=1` enables the search; the release's full pipeline control sets it to `0`. Final geometry still requires independent checks: the release recomputes the rational new-face intersection audit and verifies exact equality to the previously audited complete result.

## Measurement protocol

The +32Y input is derived from the public CT alone, using a fixed 32³ active window inside a 128³ parent and Otsu threshold 134. The threshold/input bytes are checked; labels are not used to construct this input. The window was recorded before its results, but is within an already studied cube and scroll. This is not an independent-scroll holdout.

Annotated coverage is the recorded finite set of unique labeled voxels within radius one of sampled faces; sample spacing is at most 0.75 voxel. Boundary distance uses the same 427 saved probes. These are descriptive quantitative comparisons, not proofs of sheet identity. Geometric preservation, exact new contacts, continuous geometric coverage, anatomy and text are distinct claims.

Reproduction accepts exact oriented geometry equality before reusing frozen metric/native-audit reports. It also preserves intermediate arrays and face multiplicities where checked; vertices are never welded to force agreement. The separate exact predicate uses fractions of stored binary32 coordinates and permits only intersections within the simplex of exact common corners. It checks new/source and new/new pairs, not unchanged source/source pairs or minimum clearance.

No new model training or AI inference is involved in these two software results. AI development assistance is disclosed in ATTRIBUTION.md.
