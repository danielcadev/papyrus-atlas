# Paris4 investigation closure

**The coordinate bug is fixed; cross-scan registration and ink benefit remain unvalidated.** This closes the present Paris4 investigation at the user's request and preserves its negative results. The two standalone geometry algorithms and their verified results are unchanged.

The [coordinate audit](../paris4-coordinate-audit/README.md) independently reproduces the dataset-specific NRRD native **ZYX** convention. The earlier atlas bridge incorrectly treated these indices as XYZ. Reserved-plane same-scan Pearson is approximately 0.99905. This is not a general statement that every NRRD uses that convention, and it does not certify registration between different scans.

The [exterior](../paris4-exterior-registration/README.md) and [spatial-control](../paris4-independent-controls/README.md) follow-ups retain the original Pearson >= 0.6, margin >= 0.1 and non-boundary-fit requirements. No cross-scan transform passes. The final structural trials find no reliable points under direct matching: 0/16 corner candidates and 0/12 face candidates. No fitted model, recovered letter or reading benefit is admitted. Weak third-party ink predictions do not prove blank papyrus.

Two limitations found during the final audit are disclosed in the [closure report](REPORT_EN.md): five historical pilot witnesses were mean-centered in place, so separate raw witnesses were preserved; the face selector cannot enclose its required ROI, established by an exact separating plane. Neither finding is presented as physical deformation or proof of impossibility.

## Evidence and reproduction

`evidence/` exports the six final scientific trial directories, sources, direct-match receipts, raw witnesses, acquisition references, orthogonal CT figure and independent checks unchanged. `EXPORT_PROVENANCE.json` maps published files to their original hashes. The original lab inventory is preserved verbatim; its paths resolve below `evidence/`, except the explicitly omitted internal working context, which remains unchanged in the lab. Historical absolute input paths are provenance, not portable dependencies.

For a standard-library offline integrity and saved-decision replay, from the repository root:

```bash
bash tools/run_guarded.sh paris4-closure-review-01 120 python3 -I -S "$PWD/research/paris4-closure/replay_closure.py" /tmp/paris4-closure-review-01
```

Use a new output/job name. This checks exported hashes, the saved direct-trial decisions and the exact separating-plane witness. It does not refit transforms, resample source CT or independently establish anatomy. The coordinate finding has its separate portable data replay linked above. Full scientific sampling snapshots require the recorded lab fixtures and dependencies.

The closure report's PHerc0813 face count describes the historical handoff at closure; later PHerc0813 growth does not alter Paris4 evidence. Public software/research updates do not edit a submitted application or its frozen release assets. The user reports having submitted the application; no additional form submission is performed by this update.
