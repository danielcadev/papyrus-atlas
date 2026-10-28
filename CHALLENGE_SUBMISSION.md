# Papyrus Atlas: final Progress Prize review

Papyrus Atlas is a research project working toward reconstruction of carbonized Herculaneum papyrus surfaces and verifiable ancient text. The current contribution is its pair of standalone geometry tools, **Boundary Grafting** and **Hole Recovery**, with reusable code, real-data fixtures, controls and preserved evidence.

## Reviewer entry points

- Project and instructions: https://github.com/danielcadev/papyrus-atlas
- Current source: https://github.com/danielcadev/papyrus-atlas/tree/standalone-v1
- Review edition: https://github.com/danielcadev/papyrus-atlas/releases/tag/papyrus-atlas-review-v1
- Measured before/after geometry: `figures/before-after.png`, with `figures/provenance.json` and an explicit historical/standalone correspondence caption in README.md.
- Reproduction: REPRODUCE.md; evidence and limits: VERIFICATION.md and SUBMISSION_READINESS.md.
- Wider reading milestones: PROJECT_MILESTONES.md and HISTORICAL_CONTEXT_EN.md.

The repository is public. The review edition contains unchanged algorithm code and fixtures with current English documentation and the preserved measured figure. Earlier sealed packages, tags, figures and original-language reports remain unchanged. Historical archive filenames and the `vesuvius_surface` Python namespace are retained for reproducibility.

## Team description

```text
I am submitting as an individual independent researcher under the project name Papyrus Atlas. The project's long-term objective is to reconstruct carbonized papyrus surfaces and recover verifiable ancient text. Boundary Grafting and Hole Recovery are its current standalone software contributions. Codex AI assistants helped with implementation, debugging, checks and documentation; they are not human team members. Relevant historical attribution and license notices are preserved.
```

## Contribution description

```text
Papyrus Atlas is working toward reconstructing carbonized Herculaneum papyrus surfaces and recovering verifiable ancient text. This contribution is two standalone geometry tools: Boundary Grafting and bounded whole-cycle Hole Recovery. They run with Python's standard library, without downloading, compiling or loading ScrollFiesta or its native dependencies. Their historical design and fixture lineage is attributed to experiments on public ScrollFiesta; runtime independence is not a claim of independent invention.

(1) Data. The principal software case uses graph and triangular-mesh fixtures from public PHercParis4 / Scroll 1 CT cube 01744_02256_04048, originating in the earlier predeclared +32Y Otsu experiment. Manual labels were used for post-hoc evaluation, not its Otsu input. The graph was exported from the actual historical graft call; the hole cycle is selected from the conservative source mesh alone. These are same-scroll development fixtures, not an independent-scroll holdout.

(2) Relevance to reading. Small-component filtering can discard compatible original faces, and invalid or rejected hole fills can leave useful surface incomplete. The tools address those specific failures before downstream flattening and CT sampling. They preserve geometric input; a resulting increase in readable letters has not yet been measured.

(3) Demonstrated behavior. Boundary Grafting reproduces the real graph's 27 recoveries without merging retained owners or changing geometry. It consumes supplied original-edge adjacency and recorded conflict constraints, with a completeness flag; it is not a geometric conflict detector. Hole Recovery independently adds 17 triangles to a 19-vertex boundary while retaining all 5,143 indexed source faces and source coordinates, reaching 5,160. It uses bounded search, exact rational new-contact checks, source-diagonal exclusion, boundary orientation, shape/degeneracy controls and necessary angle-fan bounds. Refusal or exhausted budgets commits no partial fill. Plain triangular OBJ and JSON mesh I/O are supported.

(4) Evidence. Eight automated tests and a real mesh-stage replay passed with the original lab directory inaccessible and Python site packages disabled. Output oriented geometry matches the historical v5 reference. The final exact new/source and new/new audit checks 267 overlapping-AABB pairs with zero forbidden contacts. The repository includes code, hashes, fixtures, before/after geometry, provenance, instructions, successful and failed records, attribution and license notices. The figure comes from the preserved historical pipeline comparison; standalone graph/mesh replay is identified separately. No source/source exact audit, complete UV map, anatomical identity or fiber continuity is claimed.

The wider project has also completed a separate 341-patch CPU reproduction of a public ink detector and an assisted Greek-reference comparison. The segment overlaps the model's published training data, and no independently verified full word resulted. PHerc0813 surface work has a 48,597-face accepted experimental descendant, but its certified square at the recorded center is 0.759246 mm versus the reader's 1.2288 mm requirement. Registration, wider support, core continuity and demonstrated ink benefit remain open milestones. Independently verifiable letters, a word and a short line are future goals, not reported discoveries.

We offer these two closely coupled geometry methods for technical review as local software improvements. Their broader significance and generalization remain for further evaluation. No new text, worldwide novelty, current-upstream superiority or prize qualification is asserted.
```

## Requirements and submission decision

Rules checked October 28, 2026: https://scrollprize.org/prizes#progress-prizes . The October deadline is October 31, 2026, 11:59 p.m. Pacific.

The public contribution has code, MIT software notices with retained attribution, real scroll-data provenance, usage examples, reproduction controls and standard triangular OBJ input/output. The two methods are bundled because they address closely coupled surface-loss and hole-fill problems. Public source access, form completeness and technically reproducible local results can be checked; award significance cannot be certified by this project.

The published virtual-unwrapping preference asks for visible fibers and evidence against sheet jumping. Those anatomical demonstrations are **not supplied by this software result**. The contribution must be judged as local mesh-processing improvements, not a proven unwrapping/reading result. Community adoption, other-scroll validation, current-upstream superiority and external reproduction remain unestablished.

All authored application text and current reviewer documentation are English. Original historical reports/logs retain their original language and bytes; HISTORICAL_CONTEXT_EN.md provides an English companion to the reading/context reports. English text does not mean historical evidence was rewritten.

The human submitter should review the completed form and terms before clicking Submit. This review, public access and GitHub publication do not submit an application or guarantee eligibility or an award.
