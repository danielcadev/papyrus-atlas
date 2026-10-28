# Vesuvius Lab — current research context

## Language and preservation

Speak with Daniel in Spanish. Write new code, comments, plans, reports, manifests and other project artifacts in English. This preference is also recorded in `AGENTS.md`.

This English working context replaces the previous Spanish working copy. Its complete historical text remains preserved, unchanged, in `research/pherc0813-fixed-strip-v1/frozen-sources/CONTEXT.md`, covered by that case's 525-file manifest. Earlier Spanish-language scientific evidence must remain unchanged; provide English editions instead of rewriting frozen files.

## Current objective

Obtain a sufficiently wide, anatomically defensible PHerc0813 surface for ink inference while retaining existing geometry, UV and safeguards. Geometry and UV admission are not evidence of anatomical identity, fibers or letters. No new PHerc0813 letters have been verified.

The last fully frozen geometric result is documented in `research/PHERC0813_FIXED_STRIP_REPORT_EN.md`, with original evidence in `research/pherc0813-fixed-strip-v1`. It preserves 47,255 source faces and UV and adds 110 faces, reaching 47,365 faces and 0.876732545 mm². Both added stages passed exact new-contact checks against all retained components and full native disk/UV certification. The final UV map has zero complete-query contacts, sigma 0.792211–1.074130 and 99.92842% of area within ±10%.

Its same-grid CT comparison gained 37 valid cells, from 10,032 to 10,069, losing none. All retained XYZ and CT float32 values remain bit-identical. The largest fully supported square **did not increase**: 0.763774500 mm versus the reference reader's 1.2288 mm requirement. Do not pad, stretch or run the reader to bypass this missing context.

A subsequent bounded coupled-endpoint experiment is documented in `research/PHERC0813_COUPLED_STRIP_REPORT.md`, with evidence in `research/pherc0813-coupled-strip-v1`. It added 16 geometric faces at its 512-proposal budget, preserved the source, replayed 16 witnesses, and passed new global exact-contact checks (zero contacts, 65 pairs). However, its incremental UV map had six contacts; single-vertex repair and component translation left two complete-query native UV contacts. The 47,381-face candidate remains rejected for UV use. The accepted 47,365-face result and supported width remain unchanged. No ink inference ran. Next: diagnose local UV constraints around old face 47274 and new faces 47375/47376, then test a separately saved local reparameterization with unchanged 3D geometry and full native gates. Do not interpret bounded search failure as impossibility.

## Latest accepted local UV repair

`research/PHERC0813_LOCAL_UV_REPORT.md` supersedes the coupled experiment's UV rejection for a separately saved map, without modifying that historical case. `research/pherc0813-local-uv-v1/constrained-v1/chart-uv.vmesh` has SHA256 `5e498c6565eb8db05d432982b8a66eec34a66523fbee8e37d453dce7d50fef34`. Joint SLSQP proposals changed only four appended UV vertices; the unchanged full native certificate passes with zero complete UV contacts at 1e-7, sigma 0.7500142821–1.1387015907, 99.90305045% area within ±10%, one disk component and no defects. All geometry and prior 47,365-face source UV bytes are retained. The accepted component now has 47,381 faces and 0.8772429757044099 mm². The same-grid downstream CT check gains seven cells (10,069→10,076), loses zero, and retains all earlier XYZ/CT values bitwise. The supported square remains 0.7637744997 mm; no ink inference ran. Next: extend supported width without discarding this accepted surface. The larger reconstruction's unrelated old contacts and anatomical limitations remain unresolved.

## Latest width-extension checkpoint

`research/PHERC0813_WIDTH_REPORT.md` and `research/pherc0813-width-v1/accepted-result-v5.json` supersede the 47,381-face checkpoint for accepted local continuation. The current descendant has **47,756 faces**, **0.8919030135495459 mm²**, and retains every preceding accepted XYZ, face and UV byte. Final geometry SHA256: `d187c1e368730c45fbd957d52c782ed7f172d296ad6196b5f6c9884a58aab95d`; UV SHA256: `666d63694fd969f86ae2cab7da7a50a32443a895b7a58968772adfda642c23f7`. Unchanged complete native UV certification passes with zero contacts, sigma 0.750012785867–1.249984132376, 99.75086111% area within ±10%, one disk and no defects. Every accepted addition has zero new retained-world exact contacts; new reference-neighbor checks also pass.

The anchored grid gains **159 samples**, **10,076→10,235**, loses zero and preserves every earlier sample XYZ bitwise. Historical sample-count-times-pitch values are **not continuous coverage certificates**. At the same exact center, the new exact continuous-square certificate improves from **0.7573222894013648 to 0.7577642647345687 mm**; this is a certified lower bound, not a global maximum. Exact UV area is **0.8912073740305383 mm²**, below the required **1.50994944 mm²** reader square, so the current chart cannot satisfy the reader at any center. No ink inference ran. The larger area and sufficient width remain open objectives.

The current evaluated square is limited by edge **[5469,5719]**, face4364, midpoint global ZYX `[8487.4951171875,3536.52099609375,5633.45947265625]`, requiring mainly **negative Y**. `limiting-arc-v2/result.json` finds no feasible clipped proposal in any of four saved references; the negative-Y reference is approximately 2.8797 voxels from the midpoint. This is a saved-reference continuity gap, not proof of absent papyrus or global infeasibility. Next: resolve that local gap in the observed band while fixing the entire accepted source; then build a coherent wider front with jointly constrained UV. Do not relax the quarter-voxel limits or force a bridge.

The width case preserves all failed/rejected branches, including a 384 MiB OOM, script failures and the rejected 366-face +Y map with 183 contacts. Native gradient stalling was not infeasibility: constrained proposals accepted a separate 62-face −Z branch. UV-aware proposals admit later geometry without moving old UVs. Three successful thin-band native references remain exploratory, not anatomical ground truth. All resources and admission gates remain unchanged. The width freeze replays the seven previous immutable chains; see its manifest and verification before treating it as frozen.

## Latest negative-Y continuity checkpoint

`research/PHERC0813_NEGY_CONTINUITY_REPORT.md` and `research/pherc0813-negy-continuity-v1/accepted-result-v12.json` supersede the width checkpoint for accepted local continuation. The original limiting indexed edge [5469,5719] is interior with exactly two incident faces. The accepted descendant has 48,565 faces, 809 additions, 0.920968303899000 mm², and every earlier XYZ/face/UV byte retained. Native full UV, retained-world and recorded reference-neighbor checks pass with zero new contacts. The larger reconstruction and anatomical identity remain uncertified.

The anchored grid gains 321 samples and loses zero with earlier XYZ bytes retained. Exact continuous square side is 0.758808766472933 mm at the recorded center; required side is 1.2288 mm. Exact chart area is 0.918493020387494 mm² versus 1.50994944 mm² required. Reader coverage gate: False. No ink inference or new verified letters. Continue from this accepted record, not rejected growth-v1; use saved limiting-arc diagnostics and validated reference inputs. Do not interpret bounded UV search failure as global infeasibility. The case freeze replays all eight previous chains; see its manifest and verification before citing it as frozen.

## Latest corner checkpoint and explicit UV-contract decision

`research/PHERC0813_CORNER_RESOLUTION_REPORT.md` and `research/pherc0813-reader-corner-v1/accepted-result-v1.json` add 12 accepted faces to the negative-Y checkpoint, reaching 48,577 with every preceding XYZ, face and UV byte retained. Native full UV, retained-world and five reference-neighbor checks pass with zero new contacts. The phase's anchored grid gains three nodes (10,559 to 10,562), loses none and retains earlier XYZ bytes. Same original-center continuous width remains 0.7588087664729335 mm; exact UV area is 0.9187570618390339 mm². Reader gate remains closed.

An exact, independently reviewed obstruction proves that corner B=19630 cannot become interior while its old oriented indexed star, XYZ and UV are fixed and sigma_min >=0.75. See `fixed-uv-obstruction-v2` and `PHERC0813_FIXED_UV_CORNER_OBSTRUCTION_REVIEW.md`. Do not repeat bounded fixed-UV fan searches. The planner finds 128 certified immutable corners; exact forbidden-center rectangles cover the closed old UV bounding box. This excludes reader-sized squares centered inside that box under the fixed-star contract, not centers outside it or other parameterizations. The prospective outside target has only 149 supported nodes and 17,012 missing; it is not coverage.

A separate **quarantined** alternative (`alternative-uv-v1`) retains all 48,577 old XYZ/faces, adds one ear and changes only UV vertices 24294 and 24295 by less than 0.008 UV units each. Full native metrics/disk/UV contacts pass using the older unchanged 47,365-face prefix; retained-world and all five neighbor checks pass. The current-prefix negative control correctly rejects because two current UV entries changed. Do not promote it or claim current-prefix UV preservation. Its separately certified same-center width is 0.7592460388423183 mm, still below 1.2288 mm. Earlier maps remain immutable evidence. Explicit user direction is pending on permitting separately certified local UV reparameterization; all geometry, metric/contact and resource protections remain mandatory either way. No ink inference or new verified letters.

## Authorized local UV continuation

After reviewing the concrete two-UV alternative, Daniel instructed: “LO QUe sea mas rapido para llegar a 1.2228 la idea es avazanr cambios grande y no hacer tatan sobringeria”. In context this authorizes the proposed separately certified local UV reparameterization. Continue in `research/pherc0813-reparameterized-width-v1`, preserving the frozen corner case and all earlier maps. The fixed-current-UV requirement is replaced only for explicit, separately saved and fully checked local UV revisions; all XYZ/faces and metric/contact/resource protections remain mandatory. Do not claim transitive UV byte preservation across this revision. The actual reference reader requirement remains 1.2288 mm. Favor broader useful growth over repeated blocked searches or extra diagnostic machinery.

## Latest accepted reparameterized-width checkpoint

`research/PHERC0813_REPARAMETERIZED_WIDTH_REPORT.md` and `research/pherc0813-reparameterized-width-v1/accepted-result-v4.json` are the current continuation. The previously quarantined one-ear/two-UV map was admitted after the explicit user choice, then UV-aware fronts added 11, one and seven faces. Final accepted count is 48,597, retaining all preceding accepted XYZ and indexed faces. All native full UV, retained-world and five reference-neighbor checks pass with zero new contacts. Original UV transitive byte preservation is correctly false across the two-coordinate revision; every old map remains immutable evidence. Subsequent accepted fronts preserve the revised UV prefix byte-for-byte.

The final exact same-center continuous width is 0.7592460388423183 mm, limited by edge [19631,24295]; required width remains 1.2288 mm. Exact chart area is 0.9191346394102973 mm², below 1.50994944 mm² required. Reader gate remains closed; rendered sample-count spans are not continuous-width proofs. No ink inference or verified letters.

The separate 48,652-face bulk branch retains 74 geometric additions and passes retained-world geometry checks, but its UV maps remain rejected: 212 initial contacts, 191 after constrained local repairs. Original-UV local revisions and a fresh full intrinsic solve did not produce an admitted map. The whole solve fails its existing metric constraints (reason7/stage6); it is not proof of universal impossibility. Do not discard its saved geometry or repeatedly rerun the unchanged failed solve.

Resume accepted growth from `accepted-result-v4.json` and `validation-v4/all-components-with-strip.vmesh`. The cached step-0.75 negative-Y apex front using the saved reader reference ended with zero additions and 208 saved complete rejection entries, skipping 501 duplicates. A useful next larger-growth experiment needs a materially different reference/front or improved joint UV solve, rather than identical passes. The corner phase is frozen at 599 files, manifest `ac82407cbaa7396b40c53a50b73231f141cd4a9ac3925fc16114f237ce10844e`; the reparameterized phase's own manifest records its final verification. All existing resource, geometry and metric/contact protections remain unchanged.

## Earlier reference limitations

- The surface reference is a guarded reconstruction from public M7, not anatomical ground truth. The full M7 flood from rank0 reaches rank2 and rank4; it was rejected for selective continuation.
- The fixed-direction preflight found −Z and +Y tranches without contacts with other saved component seeds; +Z reaches rank2, −Y reaches rank4, and ±X adds no support. This does not prove sheet identity.
- A replacement remesh with 51,149 faces failed source coverage: only 36,652 original faces remained exact, and an old vertex lies more than 0.25 voxel from every candidate AABB. Do not replace the retained source with this larger mesh.
- Reference endpoint witnesses cover vertices only, not every added face interior. Floating clipping/projection and UV search guide proposals; exact contact, topology and native metric/contact checks decide admission.
- An exact necessary-condition diagnostic found zero local obstructions among 68 boundary edges, leaving them undecided. Search rejection does not prove impossibility.
- The complete larger reconstruction remains rejected by **three native and seven exact pre-existing contacts in rank3**. All seven exact conflicts involve candidate face 211859. Its causal origin is not yet established; do not attribute it to rounding, CDT, fallback or stitching without replay.
- A conservative graft or strip certificate concerns its retained component and new contacts; it does not certify every source/source pair exactly or repair unrelated prior conflicts.

## Execution requirements

All scientific computation, builds and downloads run sequentially through `research/run_holefill_guarded.sh` and `research/run_native_guarded.py`, using the project guard:

`CPUQuota=25%`, `Nice=19`, `IOWeight=10`, `MemoryMax=384M`, `MemorySwapMax=0`, inaccessible `/dev/dri` and `/dev/kfd`, all five numerical thread limits set to 1, desktop reserve at least 3072 MiB. Do not close applications or relax limits. Historical authorization of 2 GiB applied only to an earlier ink task, not current geometry work.

Normally use Sol. Delegate only concrete independent work that saves total effort; scientific execution stays serial in the primary task. Do not use Luna. Astra is reserved for an exceptionally difficult question unresolved by Sol. Do not create agents merely to wait.

Use unique run names and output directories. Preserve successful controls, rejected candidates, timeouts and failures. Reuse byte-identical geometry and prior results instead of repeating identical tests. The GPU remains inaccessible.

## Coordinates and data

PHerc0813 volume: `20250821151723`, native voxel size 9.362 µm. Original observed CT/M7 context is 128³ at global ZYX origin `[8448,3520,5568]`. The larger observed 192³ context has origin `[8416,3488,5536]`; its central 128³ is bit-identical to the earlier data.

`research/pherc0813_io.py` reads observed public Zarr v2 chunks with strict shape, codec and coverage checks, bounded to sub-ROIs. Larger contexts are assembled sequentially in memmaps. Never replace absent chunks with fill values.

VMESH uses a 64-byte fixed header, global ZYX float32 vertices, optional float32 UV and int32 faces. Native geometry code often calls coordinates XYZ; audit scripts must explicitly follow their documented conversions. TIFF filenames encode global ZYX origins. `cube_mesh` uses 128³ cores; do not assume an arbitrary larger TIFF is a validated larger-core path. Halo input has separate size/origin rules.

The current pipeline is based on public ScrollFiesta revision `bce8a65f97652316efb084171a17d2f1f8d3ae1a`, with attribution and licenses retained. The source was extracted as an isolated experimental base, not a project Git checkout. Do not claim worldwide novelty, universal superiority or a guaranteed prize.

## Preserved earlier work

- `research/PHERC0813_CONTINUATION_REPORT.md`: historical Spanish report for 47,247 retained faces plus eight graft faces; full geometric/UV checks, observed 192³ context and rejection of the replacement remesh.
- `research/PHERC0813_EXPANDED_FLATTEN_REPORT.md`: two individually audited components flattened from a globally rejected 245,043-face reconstruction. No ink or anatomical certificate.
- `research/PHERC0813_REPAIR_V6_REPORT.md`: exact local contact guard retained 5,363 source faces plus 158 valid fills, omitting an invalid four-face proposal. Local guarding is not a global certificate. The original source opening remains.
- `research/PHERC0813_PILOT_REPORT.md`: initial 32³ PHerc0813 pilot, including exact failures and preserved controls.
- `research/scrollfiesta-comparison/hole-recovery-v5/FULL_RECOVERY_REPORT.md`: Paris4 recovery of 17 valid hole faces and preservation of 27 boundary-graft faces; continuous bidirectional geometric coverage ≤0.25 voxel. This is not an anatomical or welded-core continuity certificate.
- `research/CORE_CONTINUITY_NEXT_DECISION.md`: Paris4 winding/pitch remain unvalidated; no welding on invalid calibration. Do not loosen seam distances or infer sheet identity from shared annotation IDs.
- `research/REPAIRED_MESH_INK_REPORT.md`: public 3D ink scores were mapped descriptively, but anatomical registration gates failed. This is not verified recovered text.
- `research/WORD_REFERENCE_COMPARISON_REPORT.md`: the published editorial word ΠΟΡΦΥΡΑϹ is known, but independent local readers did not verify the entire word. Training independence and full CT/editorial correspondence were not established. Do not present it as a new discovery.
- `research/DESKTOP_MEMORY_DIAGNOSIS.md`: earlier memory measurements did not establish or rule out a leak. Applications were not closed by the agent.

The complete historical working notes and detailed artifact paths remain in the frozen context snapshots; consult those before reviving an older branch.

## Evidence and external actions

Frozen evidence chains before the current coupled experiment:

| Case | Files | Manifest SHA256 |
|---|---:|---|
| `pherc0813-pilot-v1` | 341 | `41587821ccf5398ecba8ced5e5eb356bd17dc0a1c11792ded878d3aaf215999d` |
| `pherc0813-repair-v6` | 653 | `65ee1caf1c3e1f5cfb716d27bd3b072edc2fc060ba8166da515f5b3be74fa4c6` |
| `pherc0813-expanded-v1` | 626 | `d6efb7fdebb2c0df688e609ae0f4852809ad0be9eb6d740071d93ac7c324cfed` |
| `pherc0813-continuation-v1` | 598 | `013366a5ea1bd8c87cb6ee9f1eb20597da3f219a351bf5faa335f72dea69a490` |
| `pherc0813-fixed-strip-v1` | 525 | `e4c1458dfcac9c4b394b55949f6fa065d7a2986776f153db9f49e262fb5c289e` |

Verify manifests and `evidence-verification-v1.json` before citing a phase as frozen. Preserve immutable originals, including their language.

Do not touch AnyPS5 or unrelated projects. Do not publish, submit applications, send email, create PRs, commit/push or message other chats without specific authorization. The user wants a strong prize submission, but no automatic submission or award is promised.
