# Exact CT I/O and planar ranking

This package contains two small standalone demonstrations and the recorded measurements from the original lab pipeline. The two methods are complementary infrastructure for finding and rendering papyrus sheets.

## Native CT range planning

Run `python ct_planes.py ct-plane-receipts.json`. The program regenerates the exact coalesced HTTP ranges in two recorded data sets and checks each against the local receipt archive. The data are uncompressed C-order uint8 Zarr chunks with a contiguous XY plane per Z position.

| Field | Archived range bytes | Same complete uncompressed objects | Payload reduction |
| --- | ---: | ---: | ---: |
| PHerc0800 | 445,906,944 | 574,619,648 | 22.40% |
| PHerc0175A | 359,366,656 | 513,802,240 | 30.06% |

These are recorded body bytes compared with full reads of the same objects. The receipt example runs offline. The optional `read_range` API requires HTTP 206, a matching `Content-Range` and a pinned strong ETag. Run `python test_ct_planes.py` for the local HTTP regression. This path supports uncompressed chunks only; the example does not measure HTTP overhead. A separate retained full-plane test matched the RAW, RAW-observed mask, public surface and public surface-observed mask byte for byte.

## Planar distance ranking

Run `python check_axial_index.py axial-fixture.npz` with NumPy and SciPy available. For queries on a known axial plane, any source vertex with axial separation greater than the threshold cannot affect the strict distance gate. The pruned tree and a conservative lower bound reproduce all strict threshold decisions. The real-data fixture uses a CT-derived PHerc0813 mesh subset and derived on-plane query controls.

Three prior matched pipeline replays preserved candidate geometry, selection threshold and ranking order. That stage ran 155.958→10.980 s, 29.359→2.167 s and 14.486→1.918 s. These timings are for candidate ranking alone. The included smaller demo reports its own local elapsed times. Output distances beyond the threshold can be conservative lower bounds.

## Packed rival surface reconstruction

The rival-mesh stage now stores bounded bands by profile, with prefix offsets in place of dense inverse IDs and full temporary XYZ arrays. It reconstructs coordinates only for the current batch. On two matched PHerc0191 runs, both output mesh hashes and every reported shared geometry counter were identical.

| Scan axis | Earlier peak RSS | Packed peak RSS | Peak RSS reduction | Elapsed, earlier → packed |
| --- | ---: | ---: | ---: | ---: |
| X | 4.64 GiB | 2.02 GiB | 56.48% | 55.65 → 39.73 s |
| Y | 5.35 GiB | 1.91 GiB | 64.38% | 76.25 → 53.87 s |

Peak RSS was measured with GNU time per process. Each variant ran once on the same host, input block archive and original target mesh, with order reversed between axes. See [comparison and hashes](rival-memory-comparison.json). The [replay script](replay_rival_memory.sh) uses the lab's checked PHerc0191 input archives and installed Python environment. This replay depends on those retained inputs. The range and planar-index demos above are self-contained.

## Provenance

The public source data are [Vesuvius Challenge CT scans](https://scrollprize.org/data) for PHerc0800, PHerc0175A and PHerc0813. Geometry and receipt metadata are derived from those inputs, with source pins recorded in the example files. The data retain their original [CC BY-NC 4.0 terms](https://creativecommons.org/licenses/by-nc/4.0/). Code is supplied under the accompanying MIT license.

The complete example archives, reproducible fixtures and checksums are available from the [November 2026 release](https://github.com/danielcadev/papyrus-atlas/releases/tag/progress-prize-2026-11).
