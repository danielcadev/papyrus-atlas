# Verification of the upload package

The principal clean reproduction **passed** on October 28, 2026. It began from a newly extracted, hash-verified original public archive, applied the four release patches without fuzz and compiled the native code and dependencies from source. It did not use the laboratory's precompiled ScrollFiesta library or executable.

## Results

- Production graft helper controls passed with assertions enabled.
- The CT-derived prediction bytes matched the frozen input; Otsu threshold was 134.
- Full conservative v4 and v5 pipelines retained the same 5,139-face source and reached 5,143 and 5,160 final faces.
- The final v5 VMESH SHA256 was `b93672d63891ad10c079215a5d7296f9ba4a7a5134e25750f8ba35761c11d65f`, byte-identical to the frozen full-pipeline artifact.
- The independent rational audit recomputed 267 new/source and new/new candidate pairs with zero forbidden contacts and 17 added faces.
- The full pre-graft source control reproduced its frozen digest. All its source faces were retained and exactly 27 were recovered by grafting.
- Source and executable were restored to the v5 configuration after the control build.

The complete checked reproduction took approximately 241.29 seconds under CPUQuota 25%, Nice 19, IOWeight 10, MemoryMax 384 MiB, swap zero, blocked GPU devices and one numerical thread. Its status receipt records minimum desktop available memory of 7,595.24 MiB and maximum child RSS of 254.39 MiB. The user-systemd completion reported a 379.6 MiB cgroup peak. No limit was relaxed and no application was closed.

## Independent availability and packaging checks

The upstream archive was also freshly downloaded from its public URL and verified against the pinned SHA256, then extracted and patched in a second fresh directory. Original CT and annotations were freshly downloaded from their public URLs; both lengths and SHA256 values matched. These checks establish that the documented ingredients are currently retrievable, not just present in a private local cache.

The final recipe adds reference-mesh and before-graft-fixture digest checks. They were exercised separately against the second fresh source tree without repeating the unchanged full benchmark. `verification/executed-reproduce-01.py` preserves the exact benchmark-executed version; this metadata hardening does not alter any numerical or geometric method. Its separate input-check receipt is included.

English before/after views were generated from recorded meshes with the same camera within each comparison. The first layout is retained; v2 corrects label spacing. Both input/output provenance records are included. The figure is a geometric illustration and is not a CT, fiber or ink interpretation.

`verification/` includes the benchmark, exact audit, command logs, direct-download records and resource receipts. `evidence-index.json` includes 2,084 exported historical evidence files and explicitly lists 26 external/omitted arrays or executables. One old manifest refers to a CONTEXT.md that subsequently evolved; its old and actual digests are recorded instead of falsely claiming immutable equality. Historical experiment outputs remain preserved.

The final manifest covers the released files. The archive SHA256 is provided beside the archive. The final archive is extracted into another new directory and its entire file inventory checked with the packaged verifier; that check has a separate receipt outside the sealed archive to avoid circular hashes.

## Scope

This validates reproducibility of the two principal local software improvements under the recorded setup. Historical regression, native-audit, sampled-coverage and continuous-coverage results are retained with their own scope. Metrics are reused after exact geometry equality rather than represented as new anatomical tests. No full-scroll/same-sheet certificate, verified new letters, universal success or prize is claimed. No public upload or form submission has been performed.
