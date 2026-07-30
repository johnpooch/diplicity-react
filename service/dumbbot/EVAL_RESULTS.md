# dumbbot select_orders eval results

Latest recorded run of the token-free `dumbbot_select_orders` eval, which runs
the same dataset and scorers as the harness `select_orders` eval with the
DumbBot policy as the solver. Costs zero tokens. Compare against the LLM
baseline in `harness/tasks/select_orders/EVAL_RESULTS.md`.

- **Date:** 2026-07-28
- **Solver:** `dumbbot.policy.select_orders` (rng seeded per epoch)
- **Epochs:** 20
- **Samples:** 200 completed (10 dataset samples × 20 epochs)
- **Command:** `inspect_ai.eval(dumbbot_select_orders(), model="mockllm/model", epochs=20)`

| Scorer | Metric | Value | Stderr | LLM baseline |
|---|---|---|---|---|
| legality | accuracy | 1.0000 | 0.0000 | 0.9930 |
| deduplication | accuracy | 1.0000 | 0.0000 | 0.9930 |
| coverage | accuracy | 1.0000 | 0.0000 | 0.9680 |
| support_coherence | accuracy | 1.0000 | 0.0000 | 0.9340 |
| convoy_coherence | accuracy | 1.0000 | 0.0000 | 0.9930 |
| quality_strong | accuracy | 0.7500 | 0.2500 | 0.7350 |
| quality_avoidance | accuracy | 1.0000 | 0.0000 | 0.5800 |

The structural scorers are 1.0 by construction: the policy picks options from
the engine's own enumeration, so it cannot emit an illegal, duplicated, or
uncovered order. The two `quality_*` scorers are the real signal; only 4 of the
10 dataset samples carry `ranked_options`, so their stderr is fixture-dominated,
exactly as with the LLM baseline.
