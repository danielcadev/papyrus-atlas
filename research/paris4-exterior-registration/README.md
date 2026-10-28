# Paris4 exterior registration follow-up

[Report and limitations](REPORT_EN.md). Two valid CT-only fits remain below the unchanged 0.1 margin. One derivative-support protocol error and its verifier failure are preserved and excluded from valid results. No geometry, ink or letter recovery claim changes.

From the repository root, replay the saved raw-CT correlations offline with Python's standard library:

```bash
bash tools/run_guarded.sh paris4-exterior-controls-01 120 python3 -I -S "$PWD/research/paris4-exterior-registration/replay_saved_controls.py" /tmp/paris4-exterior-controls-01
```

Use unique job and output names. This checks the saved arrays and gates only. Full lab fitting and direct scan-byte verification require the documented lab fixtures and dependencies; these are not a standalone registration reproduction package. Source data and attribution are recorded in [the coordinate audit](../paris4-coordinate-audit/README.md).

[Independent review](INDEPENDENT_REVIEW_EN.md) qualifies the reserved exterior metrics: they overlap prior initializer training and are not independent validation. The documented saved-control replay passed with site packages disabled.
