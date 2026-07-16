# Diplicity player-reliability data pack

**Purpose.** Numbers pulled from the production database to support a planning
effort on player reliability / commitment (reducing missed deadlines and game
abandonment). This document reports **data, not decisions**: Q0 is a measured
baseline; Q1–Q6 hand back distributions so a human picks thresholds later.

**Source.** Production PostgreSQL, read-only via pgweb (`/prod-query`).
**Run date.** 2026-07-16 (DB `NOW()` = 2026-07-16T23:02Z).
**Observation window.** First → last completed non-sandbox phase:
**2025-09-29 → 2026-07-16** (~9.5 months).
**Top-line volume (non-sandbox):** 926 games, 17,160 completed phases, 59,036
order-requiring phase-instances, 1,197 distinct human players, 13 bot personas.
All queries were `SELECT`-only.

---

## Definitions adopted (with sources)

| Concept | Definition adopted | Source |
|---|---|---|
| **Phase** | One turn of a game. `phase_phase` row; `type ∈ {Movement, Retreat, Adjustment}` (`PhaseType`); `status ∈ {pending, active, completed, template}` (`PhaseStatus`). A phase is "played out" once `status='completed'`. | `common/constants.py` (`PhaseType`, `PhaseStatus`); `phase/models.py` |
| **Phase-instance / seat-phase** | One `(member, phase)` pair = `phase_phasestate` row. This is the unit an NMR is measured on. | `phase/models.py` class `PhaseState` |
| **Phase that requires orders** | `phase_phasestate.has_possible_orders = TRUE` — the nation had at least one legal order that phase. Set at phase creation from `nations_with_possible_orders`. | `phase/models.py` (`create_from_adjudication_data`, field `has_possible_orders`) |
| **Submitted orders / RECEIVED** | `phase_phasestate.orders_outcome = 'received'`: the seat had ≥1 `order_order` row when the phase resolved. | `phase/models.py` `_set_orders_outcome`, `PhaseState.OrdersOutcome` |
| **NMR (no-move-received)** | `phase_phasestate.orders_outcome = 'nmr'`: `has_possible_orders=TRUE` **and** zero orders at resolution. Backfilled for historical completed phases. | `phase/models.py` `_set_orders_outcome`; migration `phase/0015_backfill_orders_outcome.py` |
| **Civil disorder (CD) on a seat** | `member_member.civil_disorder = TRUE`. Set when a seat NMRs a **Movement** phase **and its previous Movement phase (with possible orders) was also an NMR** — i.e. two consecutive Movement NMRs. Skipped for sandbox games. | `phase/models.py` `_check_civil_disorder`; migration `member/0005_member_civil_disorder.py` |
| **Abandoned game** | `game_game.status = 'abandoned'`. Set at resolution when **every** active seat (`eliminated=FALSE AND kicked=FALSE`) is in civil disorder. Sandbox excluded. | `common/constants.py` `GameStatus.ABANDONED`; `phase/models.py` `_check_abandonment`, `resolve` |
| **Finished-normally game** | `game_game.status = 'completed'` (solo victory or draw). | `common/constants.py` `GameStatus.COMPLETED`; `phase/models.py` `resolve` (Victory branch) |
| **Rated phase** *(effort's term; not a stored flag)* | The set of phase-instances that count toward a player's reliability stat: `has_possible_orders=TRUE` on a `status='completed'`, non-sandbox phase. This is exactly the denominator `get_player_stats` uses for `nmr_rate`. **There is no `rated`/`is_rated` column** — this is a derived definition. | `user_profile/utils.py` `get_player_stats` |
| **Reliability tier** *(computed, not stored)* | `get_player_stats(user)['reliability_tier']`, derived live per request: `"new"` if `total_games < 10`; `"reliable"` if `nmr_rate ≤ 0.10` **and** `cd_rate ≤ 0.10`; else `None` ("undefined"). Window = last **10 completed non-sandbox games** (`RELIABILITY_GAME_WINDOW`), thresholds `RELIABLE_NMR_THRESHOLD=0.1`, `RELIABLE_CD_THRESHOLD=0.1`. `nmr_rate` is over rated phases in those games; `cd_rate` is the fraction of those games with `civil_disorder=TRUE`. | `user_profile/utils.py` |
| **Game-join reliability gate** | `game_game.min_reliability ∈ {open, reliable_and_new, reliable_only}` (`MinReliability`), enforced by `MeetsReliabilityRequirement` via `tier_allows_min_reliability`. | `common/constants.py` `MinReliability`; `common/permissions.py`; `user_profile/utils.py` |
| **Bot player** | Member whose `user_id` has a `bot_profile_botprofile` row (13 personas + the `diplicitybot` base user). Excluded from all human-behaviour figures below. | `bot_profile/models.py`, `bot_profile/constants.py` |

### Ambiguities / judgement calls (read before using the numbers)

1. **"Rated phase" is a reconstruction.** No stored flag exists. I use the exact
   filter `get_player_stats` applies (`has_possible_orders` on completed
   non-sandbox phases). If the effort later defines rated phases differently
   (e.g. Movement-only, or excluding terminal phases), every Q1/Q2 count shifts.
2. **Tier window is games, not phases.** The *current* system rates on the last
   **10 games**; the effort is exploring a **rated-phases** threshold (6–20).
   These are different units — Q1(a) reports the phase distribution the effort
   asked for, but it is not what production keys on today.
3. **`civil_disorder` is a mutable current-state flag, not a historical record.**
   It is reset to `FALSE` when a CD seat is later eliminated
   (`_reconcile_civil_disorder_eliminations`), and it did not exist before
   migration `member/0005`. So counting current `civil_disorder=TRUE` **undercounts**
   seats that were abandoned (see Q4 — 29 abandoned games now show 0 CD seats).
4. **Deleted-account members are kept as real players.** `member.user_id IS NULL`
   (user deleted; FK `SET_NULL`) represents genuine quit/abandon behaviour, so
   these rows are **included** in the pooled Q0 baseline (they NMR at 51.9%).
   They are **excluded** from per-player distributions (Q1–Q3) because a null
   user can't be grouped into a person.
5. **Terminal phases carry a NULL outcome.** The last phase of a finished game is
   `status='completed'` but is never resolved, so its `orders_outcome` stays NULL
   (974 rows, ~1.6% of the Q0 denominator). Consistent with `get_player_stats`,
   these count in the denominator as non-NMR. They mildly *lower* the NMR rate.

---

## Q0 — True NMR baseline (decision-grade)

**Metric.** NMR rate = `orders_outcome='nmr'` phase-instances ÷ order-requiring
phase-instances (`has_possible_orders=TRUE`), over `status='completed'`,
non-sandbox phases, **bots excluded** (humans + deleted accounts kept).

| Cohort | Denominator | NMR | **NMR rate** |
|---|---:|---:|---:|
| All-time, **excluding** abandoned games (flattered) | 56,179 | 17,157 | **30.5 %** |
| **All-time, INCLUDING abandoned games — HONEST BASELINE** | 58,802 | 18,320 | **31.2 %** |
| Last 30 days, excluding abandoned *(reproduces the prior figure)* | 27,856 | 6,407 | **23.0 %** |
| Last 30 days, including abandoned | 28,547 | 6,735 | 23.6 % |

### Reproducing the prior 23.46 %

The prior 23.46 % reproduces as a **recent ~30-day window** number, not an
all-time one: last-30-day NMR is **23.0 %** excluding abandoned and **23.6 %**
including — 23.46 % sits between them. Monthly pooled rates confirm the window
effect (by phase `created_at`, humans, incl. abandoned): 2026-05 ≈ 36 %,
2026-06 ≈ 32 %, 2026-07 ≈ 23 %. The recent window reads low because games created
recently are **right-censored**: the NMR-heavy late phases of games that will
eventually die (and long-deadline games generally) have not accumulated yet.

### What actually flatters the prior number

- **Excluding abandoned games:** small — +0.6 to +0.7 pp (abandoned games are
  only 84 of 926 and ~4 % of phase-instances). Real, but not the main distortion.
- **Using a recent window instead of all-time:** large — **~+8 pp** (23 % → 31 %).

**Honest baseline the target should be measured against: ~31 % NMR**
(all-time, including abandoned games, 18,320 / 58,802 order-requiring
phase-instances, 2025-09-29 → 2026-07-16). If a recent-window KPI is preferred,
state the window explicitly and **include abandoned games**.

Context (all-time, non-bot, incl. abandoned): NMR by phase type —
Movement 31.6 %, Retreat 40.3 %, Adjustment 20.2 %. By final game status —
completed 32.7 %, active 17.1 %, abandoned 44.3 %. Bots NMR at 0.4 %
(234 instances); deleted accounts at 51.9 % (920 instances).

```sql
-- Honest baseline (swap the WHERE on g.status for the excl-abandoned row)
SELECT COUNT(*) AS denom,
       COUNT(*) FILTER (WHERE ps.orders_outcome='nmr') AS nmr,
       ROUND(100.0*COUNT(*) FILTER (WHERE ps.orders_outcome='nmr')/COUNT(*),2) AS nmr_pct
FROM phase_phasestate ps
JOIN phase_phase pp ON ps.phase_id=pp.id
JOIN game_game g   ON pp.game_id=g.id
JOIN member_member m ON ps.member_id=m.id
LEFT JOIN bot_profile_botprofile bp ON bp.user_id=m.user_id
WHERE pp.status='completed' AND ps.has_possible_orders=TRUE
  AND g.sandbox=FALSE AND bp.id IS NULL;              -- incl. abandoned
-- excl. abandoned: add  AND g.status <> 'abandoned'
-- last 30 days:    add  AND pp.created_at >= NOW() - INTERVAL '30 days'
```

---

## Q1 — Tier calibration

Player = distinct `user_id`, bots and deleted accounts excluded. Rated phase as
defined above. **1,047 players** have ≥1 rated phase.

### Q1(a) Rated-phases-played per player

Percentiles: mean 55.3, min 1, **p10 6, p25 11, p50 22, p75 49, p90 122,
p95 220, max 1,709.**

| Rated phases | Players | % | Cumulative % |
|---|---:|---:|---:|
| 1–5 | 92 | 8.8 | 8.8 |
| 6–10 | 147 | 14.0 | 22.8 |
| 11–20 | 257 | 24.5 | 47.4 |
| 21–40 | 238 | 22.7 | 70.1 |
| 41–80 | 154 | 14.7 | 84.8 |
| 81–160 | 80 | 7.6 | 92.5 |
| 161+ | 79 | 7.5 | 100.0 |

Reads for the "undefined → rated" exit threshold (the 6–20 band under
consideration): a threshold of **6** leaves 8.8 % of players "undefined";
**10** leaves 22.8 %; **20** leaves 47.4 %.

### Q1(b) Per-player NMR rate distribution

Per-player rate = that player's `nmr / rated_phases` pooled across all their
games (mirrors `get_player_stats.nmr_rate` but over all history, not the last-10
window).

| Per-player NMR rate | All players (n=1,047) | ≥10 rated phases (n=831) |
|---|---:|---:|
| 0 % | 14.2 % | 10.7 % |
| (0, 5 %] | 6.3 % | 7.9 % |
| (5, 10 %] | 5.2 % | 6.5 % |
| (10, 20 %] | 8.3 % | 9.7 % |
| (20, 35 %] | 9.6 % | 11.8 % |
| (35, 50 %] | 9.7 % | 10.1 % |
| (50, 75 %] | 14.6 % | 13.1 % |
| (75, 100 %] | 32.0 % | 30.1 % |

Percentiles (all players): **p10 0 %, p25 9.1 %, p50 45.5 %, p75 88.1 %,
p90 100 %, mean 48.4 %**. For ≥10 rated phases: p25 10 %, p50 39.5 %, p75 85 %,
mean 46.2 %.

The distribution is **strongly bimodal**: a large clean cluster (≈25 % of
players at ≤10 %) and a large chronic-abandoner cluster (≈30 % above 75 %),
with a thin middle. A cut-point near the current `RELIABLE_NMR_THRESHOLD` of
10 % puts ~25 % of players in "low-NMR". Any high/medium/low scheme should note
that a middle band is genuinely sparse — the population is closer to
"reliable vs. gone" than a smooth gradient. **Caveat:** this rate counts every
post-CD phase as an NMR (a CD seat keeps generating NMR phase-instances until
the game ends), so chronic early-quitters are pushed toward 100 %; the number
overstates ongoing-player miss rates and is not directly comparable to the Q0
pooled 31 %.

### Q1(c) Window-size sensitivity (one bad phase, most-recent N rated phases)

| Window N | One NMR moves rate by | Players with < N rated phases (window can't fill) |
|---|---:|---:|
| 5 | 20.0 pp | 8.0 % |
| 6 | 16.7 pp | 8.8 % |
| 8 | 12.5 pp | 14.0 % |
| 10 | 10.0 pp | 20.6 % |
| 12 | 8.3 pp | 25.8 % |
| 15 | 6.7 pp | 33.8 % |
| 20 | 5.0 pp | 45.6 % |

Trade-off is explicit: a short window (N=6) reacts hard to a single miss
(+16.7 pp) but almost every player can fill it (8.8 % short). A long window
(N=20) is smooth (5 pp/miss) but nearly half of players don't have 20 rated
phases yet, so it degenerates toward the game-count gate.

```sql
-- Q1(a): rated phases per player (histogram / percentiles built from this CTE)
SELECT m.user_id, COUNT(*) AS rated_phases,
       COUNT(*) FILTER (WHERE ps.orders_outcome='nmr') AS nmr
FROM phase_phasestate ps
JOIN phase_phase ph ON ps.phase_id=ph.id
JOIN game_game g    ON ph.game_id=g.id
JOIN member_member m ON ps.member_id=m.id
LEFT JOIN bot_profile_botprofile bp ON bp.user_id=m.user_id
WHERE ph.status='completed' AND ps.has_possible_orders=TRUE
  AND g.sandbox=FALSE AND m.user_id IS NOT NULL AND bp.id IS NULL
GROUP BY m.user_id;
-- Q1(b) re-uses this; per-player rate = nmr::float/rated_phases.
```

---

## Q2 — Penalty-free concede (minimum phases played)

Two units. **Per player (user):** see Q1(a) — median 22 rated phases lifetime.
**Per seat (one `member`, i.e. one game):** the relevant unit for "how far into
*this* game has the player gone before conceding". 3,803 seats (bots excluded,
completed phases).

Per-seat percentiles: rated phases mean 15.5, **p10 4, p25 9, p50 14, p75 20,
p90 27, max 198**; phases-present (incl. no-order phases) mean 25.8, p50 24.

| Rated phases in the seat | Seats | % | Cumulative % |
|---|---:|---:|---:|
| 1–2 | 155 | 4.1 | 4.1 |
| 3–5 | 316 | 8.3 | 12.4 |
| 6–10 | 807 | 21.2 | 33.6 |
| 11–20 | 1,593 | 41.9 | 75.5 |
| 21–40 | 882 | 23.2 | 98.7 |
| 41+ | 50 | 1.3 | 100.0 |

A minimum-phases-played bar for penalty-free concede reads directly off the
cumulative column: a bar of **2** covers 4.1 % of seats, **5** covers 12.4 %,
**10** covers 33.6 %. **Caveat:** this counts seats in *completed* phases only,
so a player who quit in a still-active game isn't represented; the low bands are
therefore a slight undercount of genuinely-short participations.

```sql
SELECT m.id AS member_id,
       COUNT(*) FILTER (WHERE ps.has_possible_orders) AS rated_phases,
       COUNT(*) AS phases_present
FROM member_member m
JOIN game_game g ON m.game_id=g.id
JOIN phase_phasestate ps ON ps.member_id=m.id
JOIN phase_phase ph ON ps.phase_id=ph.id
LEFT JOIN bot_profile_botprofile bp ON bp.user_id=m.user_id
WHERE ph.status='completed' AND g.sandbox=FALSE AND bp.id IS NULL
GROUP BY m.id;
```

---

## Q3 — Concurrent-play caps

Current snapshot: active, non-eliminated, non-kicked seats per player in
`status='active'` non-sandbox games. **380 players** are currently in ≥1 active
game.

| Concurrent active games | Players | % |
|---|---:|---:|
| 1 | 211 | 55.5 |
| 2 | 60 | 15.8 |
| 3 | 32 | 8.4 |
| 4–5 | 34 | 8.9 |
| 6–10 | 37 | 9.7 |
| 11–20 | 6 | 1.6 |

Percentiles: mean 2.47, **p50 1, p75 3, p90 6, p95 7, p99 15, max 19**.

**No stored tier field exists**, so no true tier split is possible. As the more
decision-relevant cut, here is current concurrency vs. the player's pooled
lifetime NMR rate:

| Concurrency | Players | Pooled NMR rate |
|---|---:|---:|
| 1 | 191 | 30.2 % |
| 2 | 55 | 17.8 % |
| 3 | 32 | 17.3 % |
| 4–5 | 34 | 21.1 % |
| 6+ | 43 | 11.7 % |

The correlation runs **opposite** to the intuition behind a cap: high-concurrency
players are *more* reliable (6+ games → 11.7 % NMR), while single-game players are
the least reliable (30.2 %), because the single-game bucket is full of
one-and-done joiners. A concurrency cap would mostly constrain the most engaged,
reliable players. **Caveat:** current concurrency joined to lifetime NMR is a
coarse cross-section, not a within-player time series.

```sql
SELECT m.user_id, COUNT(*) AS active_games
FROM member_member m JOIN game_game g ON m.game_id=g.id
LEFT JOIN bot_profile_botprofile bp ON bp.user_id=m.user_id
WHERE g.status='active' AND g.sandbox=FALSE
  AND m.eliminated=FALSE AND m.kicked=FALSE
  AND m.user_id IS NOT NULL AND bp.id IS NULL
GROUP BY m.user_id;
```

---

## Q4 — Corpse threshold (dead seats per game)

Finished games only (`completed` + `abandoned`, non-sandbox, non-kicked seats):
**522 completed, 84 abandoned = 606 games.** "Dead seat" = `civil_disorder=TRUE`
OR `eliminated=TRUE`. Because absolute counts confound game size (a 7-player vs
a 15-player variant), the **size-normalized** view is the reliable one:

| Dead seats (% of game's seats) | Games | Finished | Died | % died |
|---|---:|---:|---:|---:|
| 0 % | 271 | 242 | 29 | 10.7 |
| (0, 25 %] | 17 | 17 | 0 | 0.0 |
| (25, 50 %] | 103 | 103 | 0 | 0.0 |
| (50, 75 %] | 132 | 132 | 0 | 0.0 |
| (75, 100 %] | 83 | 28 | 55 | 66.3 |

Sharp signal: games routinely **finish** after losing up to ~75 % of their seats
to CD/elimination; death rate only jumps at the extreme (**>75 % dead → 66 %
died**). Absolute-count view (for reference) is noisier and non-monotonic — e.g.
2 dead seats → 41 % died, 3–6 dead → <11 %, 7 dead → 67 % — precisely because it
ignores game size.

**Caveats (important):**
- The 29 deaths in the "0 %" band are an artefact: `civil_disorder` is reset to
  `FALSE` on elimination, and the flag didn't exist before migration
  `member/0005`, so **29 of 84 abandoned games now show 0 CD seats** (verified
  directly). A robust historical "dead seat" measure should be reconstructed
  from **consecutive Movement NMRs** (the CD trigger) via `orders_outcome`, not
  from the live flag — recommend building that before setting a corpse threshold.
- `eliminated` mixes combat elimination (normal play) with abandonment, inflating
  the dead-seat count for healthy games; this pushes the (0,75 %] bands *down* in
  death rate, so the true "survives heavy losses" story is if anything stronger.

```sql
WITH gm AS (
  SELECT g.id, g.status,
    (SELECT COUNT(*) FROM nation_nation n
       WHERE n.variant_id=g.variant_id AND n.non_playable=FALSE) AS seats,
    COUNT(*) FILTER (WHERE m.civil_disorder OR m.eliminated) AS dead
  FROM game_game g JOIN member_member m ON m.game_id=g.id
  WHERE g.sandbox=FALSE AND g.status IN ('completed','abandoned') AND m.kicked=FALSE
  GROUP BY g.id, g.status, g.variant_id)
SELECT width_bucket(1.0*dead/NULLIF(seats,0), 0, 1.0001, 4) AS quarter,
       COUNT(*) games,
       COUNT(*) FILTER (WHERE status='abandoned') died
FROM gm GROUP BY 1 ORDER BY 1;
```

---

## Q5 — Auto-expiry windows (stalled pre-start games)

`status='pending'`, non-sandbox = never filled/started. Game size = playable
nation count of the variant; age = `NOW() - created_at`. **149 pending games.**

| Game size (seats) | Pending games | Avg seats joined | Median age (d) | p90 age (d) | Max age (d) |
|---|---:|---:|---:|---:|---:|
| 2 | 15 | 0.7 | 32.3 | 141.9 | 212.2 |
| 3 | 8 | 1.0 | 95.0 | 220.2 | 263.4 |
| 5 | 8 | 2.3 | 12.3 | 27.5 | 32.3 |
| 6 | 4 | 2.3 | 20.1 | 46.5 | 51.4 |
| 7 | 102 | 1.5 | 39.2 | 231.2 | 273.3 |
| 8 | 2 | 1.5 | 3.2 | 4.2 | 4.4 |
| 10 | 8 | 2.1 | 34.5 | 63.9 | 76.1 |
| 15 | 2 | 6.5 | 8.8 | 8.8 | 8.8 |

The bulk is **7-seat (classical) games — 102 of 149** — sitting a median 39 days
and up to 273 days with only ~1.5 of 7 seats filled: clear candidates for
size-scaled auto-expiry. Small (2–3 seat) games also linger for months. **Caveat:**
small per-size samples outside size 7 (n as low as 2); "avg seats joined" includes
the creator, so these are genuinely near-empty. Median age already exceeds a month
for most sizes, so any reasonable expiry window would reclaim a large fraction.

```sql
SELECT (SELECT COUNT(*) FROM nation_nation n
          WHERE n.variant_id=g.variant_id AND n.non_playable=FALSE) AS seats,
       EXTRACT(EPOCH FROM (NOW()-g.created_at))/86400.0 AS age_days,
       (SELECT COUNT(*) FROM member_member m WHERE m.game_id=g.id) AS joined
FROM game_game g WHERE g.status='pending' AND g.sandbox=FALSE;
```

---

## Q6 — Mustering deadline

**No pre-start mustering / confirmation step exists, so there is no such data.**
A game is `pending` until `members.count()` equals the variant's playable-nation
count, at which point `start_if_full()` starts it automatically
(`game/models.py:693`). Joining a game *is* the commitment; there is no separate
"ready/confirm" flag on `member_member` (its booleans are `won, drew, eliminated,
kicked, civil_disorder, seeking_replacement` — none pre-start). The only
"confirm" in the codebase is per-phase **order** confirmation during active play
(`Game.phase_confirmed`, `PhaseState.orders_confirmed`), which is not a mustering
step. If a mustering deadline is desired, it would be **new behaviour** with no
historical baseline to calibrate against.

---

## Caveats — reliability of each answer

| Question | How well the data supports it | Key risk |
|---|---|---|
| **Q0 baseline** | **Strong.** Direct, backfilled `orders_outcome`; method validated by reproducing the prior figure as a window artefact. | Terminal phases (NULL outcome, ~1.6 %) counted as non-NMR; consistent with the app's own stat. |
| **Q1(a) rated phases** | **Strong.** Simple count over a well-defined set. | "Rated phase" is reconstructed, not a stored flag. |
| **Q1(b) per-player NMR** | **Moderate.** Distribution is real but inflated at the top by post-CD phase accumulation; not comparable to Q0's 31 %. | Chronic quitters pushed toward 100 %; middle band genuinely sparse. |
| **Q1(c) window sensitivity** | **Strong** (arithmetic + fill-rate from real data). | — |
| **Q2 phases per seat** | **Strong** for completed phases. | Excludes seats in still-active games → slight undercount of short stints. |
| **Q3 concurrency** | **Moderate.** Current snapshot is solid; the NMR cross-tab is a coarse cross-section. | No stored tier → true tier split not possible; correlation is cross-sectional. |
| **Q4 corpse threshold** | **Moderate.** Size-normalized signal is sharp and decision-useful. | `civil_disorder` flag is mutated/pre-instrumentation (29/84 abandoned games show 0 CD); `eliminated` conflates combat with abandonment. Rebuild dead-seat from consecutive Movement NMRs before finalizing. |
| **Q5 auto-expiry** | **Good for size 7; weak elsewhere.** | Small samples for sizes ≠ 7 (n as low as 2). |
| **Q6 mustering** | **N/A — no such step exists.** | — |
