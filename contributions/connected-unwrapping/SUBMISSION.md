# Progress Prize submission draft

**Title**\
Recovering connected charts for virtual papyrus unwrapping

**Contribution**\
We worked on PHerc0800 volume 20250521135224 and PHerc0175A volume 20250521115057, both at 8.64 µm. On physically checked native sheets, a UV crop or an overlap-removal pass can break the only connection between large areas. We provide two tools for restoring continuity while retaining original mesh coordinates.

- **PHerc0800, before UV fitting.** The selector follows original shared edges outside a failing crop while excluding the first fit's mandatory vetoes. Against our earlier fixed crop on the same reconstruction, connected area after UV contact removal rose from 64.659 to 104.166 mm² and the chart retained a conservative 26.074 mm native rail.
- **PHerc0175A, after UV fitting.** A fixed-map tool restores a short connecting path and removes its conflicts. On the same audited UV map, the largest component rose from 77.749 to 100.981 mm². It retained the full 28.005 mm rail with native coordinates and UV unchanged.

Both recovered charts passed independent UV certification with zero invalid faces or overlaps. The submission includes both runnable replays, attributable fixtures, exact mesh lineage, a UV-bearing OBJ, measured comparisons and CT evidence. These are two geometry results, with no confirmed new text. Each comparison uses an earlier stage of our own workflow on the same native input.

**Submission links**\
Use the public repository URL for the code and README and a public release URL for the fixtures, meshes and evidence archive.

**Form**\
[November 2026 Progress Prizes](https://docs.google.com/forms/d/e/1FAIpQLSeB6MC_--4UCCEGc3zalX57-uE4puRcE_vJoYJCrEt4uYaaaw/viewform)
