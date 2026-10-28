# Paris4 spatial control audit

[Report](REPORT_EN.md) and [independent review](INDEPENDENT_REVIEW_EN.md). Two zero-residual-start affine fits fail the unchanged margin>=0.1 and parameter-boundary controls. Newly withheld CT targets are spatially disjoint from current training; they are not independent scans or annotated anatomical landmarks. No ink or letter recovery is demonstrated.

From the repository root, replay saved CT correlations and decisions offline with Python's standard library:

```bash
bash tools/run_guarded.sh paris4-independent-saved-01 120 python3 -I -S "$PWD/research/paris4-independent-controls/replay_saved_controls.py" /tmp/paris4-independent-saved-01
```

Use a unique job/output name. This reproduces saved-array correlations and gates only. Full fitting and direct CT sampling require the recorded lab fixtures, NumPy and SciPy. Original public source attribution and license references remain in the [coordinate audit](../paris4-coordinate-audit/README.md).

The documented saved-control replay passed with site packages disabled. Its receipt is preserved in `portable-replay-verification.json`.
