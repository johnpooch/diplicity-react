# select_orders eval results

Latest recorded run of the `select_orders` harness evals. Update this file when
a new baseline run is taken.

- **Date:** 2026-07-28
- **Model:** `anthropic/claude-haiku-4-5`
- **Epochs:** 100
- **Samples:** 1000 completed (10 dataset samples × 100 epochs)
- **Command:** `inspect_ai.eval(select_orders(), epochs=100)` (the `run_evals`
  command exposes no `--epochs` flag)

| Scorer | Metric | Value | Stderr |
|---|---|---|---|
| legality | accuracy | 0.9930 | 0.0026 |
| deduplication | accuracy | 0.9930 | 0.0026 |
| coverage | accuracy | 0.9680 | 0.0117 |
| support_coherence | accuracy | 0.9340 | 0.0583 |
| convoy_coherence | accuracy | 0.9930 | 0.0026 |
| quality_strong | accuracy | 0.7350 | 0.1439 |
| quality_avoidance | accuracy | 0.5800 | 0.2390 |

The two `quality_*` scorers now report a real signal (`quality_strong` 0.74,
`quality_avoidance` 0.58). They previously showed a degenerate `0.0000
ranked_accuracy`: the custom `ranked_accuracy` metric filtered `NOANSWER` and
compared against the string label `CORRECT`, but inspect reduces every score to
a float before metrics run (`NOANSWER`/`INCORRECT` → 0.0, `CORRECT` → 1.0), so
the filter and comparison never matched and the metric floored to 0.0. Fixed by
scoring un-ranked samples with `Score.unscored()` (the NaN sentinel inspect
excludes from metrics) and using the standard `accuracy()` metric, which then
averages over just the ranked samples.

Only 4 of the 10 dataset samples carry `ranked_options`, so the `quality_*`
stderr stays high (fixture-level variance dominates): the model reliably finds
the strong order in some positions and reliably misses it in others. Adding more
ranked fixtures — e.g. via the `dump_phase` harvesting loop — will tighten these.
