# select_orders eval results

Latest recorded run of the `select_orders` harness evals. Update this file when
a new baseline run is taken.

- **Date:** 2026-07-28
- **Model:** `anthropic/claude-haiku-4-5`
- **Epochs:** 100
- **Samples:** 1000 completed (10 dataset samples × 100 epochs)
- **Command:** `python manage.py run_evals` (epochs=100 supplied ad hoc)

| Scorer | Metric | Value | Stderr |
|---|---|---|---|
| legality | accuracy | 0.9920 | 0.0036 |
| deduplication | accuracy | 0.9920 | 0.0036 |
| coverage | accuracy | 0.9770 | 0.0101 |
| support_coherence | accuracy | 0.9360 | 0.0542 |
| convoy_coherence | accuracy | 0.9920 | 0.0036 |
| quality_strong | ranked_accuracy | 0.0000 | 0.1315 |
| quality_avoidance | ranked_accuracy | 0.0000 | 0.1304 |

The legality and coherence scorers are strong (0.94–0.99). The two `quality_*`
scorers report 0.0000 ranked_accuracy — investigate before treating this as a
true quality signal (the ranked scorers may be degenerating rather than
reflecting genuinely poor ordering).
