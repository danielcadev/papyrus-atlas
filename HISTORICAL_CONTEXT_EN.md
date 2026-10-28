# English companion to the historical reading and surface reports

This is an English summary edition for reviewers, not a replacement or a word-for-word translation of the frozen originals. The original reports remain unchanged in `project-context-evidence/`; `MILESTONE_EVIDENCE.json` records their hashes. These are separate research experiments, not runtime modules of the standalone geometry tools.

## Public ink-detector reproduction

Original: [INK_REPRODUCTION_REPORT.md](project-context-evidence/INK_REPRODUCTION_REPORT.md).

The lab reproduced the public ScrollPrize ink_9um detector on an already flattened public PHercParis4 surface, segment 20231016151002. The pinned model/code and checkpoint digest are recorded in the original report. The CT surface-volume input was pooled to 9.6 micrometers; the model used 17 central depth planes, 128-square patches, stride 64, CPU float32, batch one and Hann blending. No new model was trained.

The expanded 21-by-768-by-2048 surface input was acquired and preserved. One inference attempt stopped after 302/341 patches because the desktop reserve fell below its required level. A separately saved retry, using identical input and parameters, completed all 341 patches. Its probability file SHA256 is `d59e924ceabebdf6aaf1ba62552c17daf0b814f33c1c53841c21fc4ae20f3141`. The complete retry took about 341.50 seconds, with child RSS about 517.60 MiB. It used the separately authorized historical 2GiB ink envelope; this does not alter today's 384MiB geometry limits.

The segment was used in published training, and region selection involved public annotations and development inspection. Recorded label agreement (including Dice about 0.920356 on supervised pixels) is assisted development agreement, not held-out performance or transcription accuracy. A constant-input control produced spatial structure, further limiting interpretation of isolated model shapes. Independent local readers did not verify a full word. The pipeline reproduces a public technical baseline, not newly deciphered text or an independently trained ink model.

## Known-word comparison

Original: [WORD_REFERENCE_COMPARISON_REPORT.md](project-context-evidence/WORD_REFERENCE_COMPARISON_REPORT.md).

Local predicted shapes were compared with published reference material for the Greek word ΠΟΡΦΥΡΑϹ. Some shapes are compatible with that reference, but the interpretation is assisted and not a complete independent letter-by-letter reading. In particular, an expected upsilon remains T-like locally; other strokes remain uncertain. The earlier negative/uncertain readings are preserved rather than replaced by the expected word.

Image-registration attempts against official reference panels did not pass their declared gates. A separate coordinate check against a modern preview, using metadata-fixed scale/origin rather than a fitted transform, reached Pearson about 0.888157 and passed its stated local controls. That establishes a limited 2D consistency result, not original-CT registration, editorial correspondence, anatomical identity or independence from shared training/model biases. A bounded depth probe preserved all five tested windows and did not resolve the ambiguous letter. No new word is claimed.

## Repaired meshes, CT profiles and public ink scores

Original: [REPAIRED_MESH_INK_REPORT.md](project-context-evidence/REPAIRED_MESH_INK_REPORT.md).

The lab sampled real CT and a published volumetric ink-score field on before/after geometry. Common-face CT profiles were bit-identical, and the technical sampling connection was replayed. The 27 graft faces had candidate signal in that published field; the 17 hole faces had very low scores. These were raw published uint8 scores, not calibrated probabilities or a newly executed independent ink detector.

Old-to-modern CT association failed the predeclared local consistency/margin gates. Thus the predicted signal was not accepted as anatomically associated with our repaired surface. No affine was tuned to obtain ink. The available mesh context was also too small for the 2D reader, so it was not stretched, padded or passed through the reader. These results do not show rescued letters or improved ink accuracy. The accepted geometry remains separately supported by its geometric checks.

## Core continuity

Original: [CORE_CONTINUITY_NEXT_DECISION.md](project-context-evidence/CORE_CONTINUITY_NEXT_DECISION.md).

Saved preflight geometry retained 13,346 faces and ten disk components without measured conflicts under its stated audit. No weld was attempted. Candidate seam chains still lacked supported anatomical correspondence and winding/pitch calibration; the recorded calibration accepted zero of 81 profiles and did not produce a valid pitch. An axis estimate by itself did not arm a supported physical correspondence.

The lab did not use an invented pitch, disable the winding gate or enlarge tolerances to force bridges. Core continuity remains unresolved. Next acceptance requires supported local winding calibration, preserved source, and all contact/topology/ambiguity checks. A clean geometric preflight is not a proof that two cores trace the same papyrus sheet.

## PHerc0813 surface support

Original English report: [PHERC0813_REPARAMETERIZED_WIDTH_REPORT.md](project-context-evidence/PHERC0813_REPARAMETERIZED_WIDTH_REPORT.md).

The accepted experimental descendant retains earlier accepted 3D geometry and reaches 48,597 faces. An explicitly authorized local revision changed two old UV coordinates; original UV byte preservation is therefore not claimed across that revision, and old maps remain saved. Subsequent accepted fronts retain the revised prefix. The exact continuous square at the recorded center is 0.7592460388423183 mm, below the reader requirement of 1.2288 mm. This is not a claim of the globally largest supported square.

A larger 48,652-face geometry branch has rejected UV maps, including 191 remaining contacts after local proposals. It is not an accepted substitute. No PHerc0813 reader inference or verified letters resulted. The work remains a path toward supported surface context, anatomy and reading, not an achieved First Letters result.
