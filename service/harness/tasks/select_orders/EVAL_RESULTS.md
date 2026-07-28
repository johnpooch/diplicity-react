# select_orders eval results

Latest recorded run of the `select_orders` harness evals. Update this file when
a new baseline run is taken.

- **Date:** 2026-07-28
- **Model:** `anthropic/claude-haiku-4-5`
- **Epochs:** 1 (single-epoch smoke run)
- **Samples:** 10 dataset samples
- **Command:** `python manage.py run_evals`

| Scorer | Metric | Value | Stderr |
|---|---|---|---|
| legality | accuracy | 1.0000 | 0.0000 |
| deduplication | accuracy | 1.0000 | 0.0000 |
| coverage | accuracy | 1.0000 | 0.0000 |
| support_coherence | accuracy | 0.9000 | 0.1000 |
| convoy_coherence | accuracy | 1.0000 | 0.0000 |
| quality_strong | accuracy | 0.7500 | 0.2500 |
| quality_avoidance | accuracy | 0.5000 | 0.2887 |

The two `quality_*` scorers now report a real signal. They previously showed a
degenerate `0.0000 ranked_accuracy`: the custom `ranked_accuracy` metric filtered
`NOANSWER` and compared against the string label `CORRECT`, but inspect reduces
every score to a float before metrics run (`NOANSWER`/`INCORRECT` → 0.0,
`CORRECT` → 1.0), so the filter and comparison never matched and the metric
floored to 0.0. Fixed by scoring un-ranked samples with `Score.unscored()` (the
NaN sentinel inspect excludes from metrics) and using the standard `accuracy()`
metric, which then averages over just the ranked samples.

This is a single-epoch smoke run — only 4 of the 10 samples carry
`ranked_options`, so the `quality_*` values are low-N and noisy. Take a
multi-epoch run for a stable baseline.
