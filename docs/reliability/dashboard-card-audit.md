# Reliability dashboard — audit of the ten cards live today

Audit of the cards currently on the Reliability dashboard, taken at `9cbb3c9`.
All figures are from the production database on 2026-08-03 via pgweb.

Resolves [#1140](https://github.com/johnpooch/diplicity-react/issues/1140) under
[Map: a dashboard that shows whether reliability work is working](https://github.com/johnpooch/diplicity-react/issues/1139).

---

## Verdicts at a glance

| # | Card | Reads | Verdict | Corrected |
|---|---|---|---|---|
| 1 | Total Users | 3,233 | Wrong | 3,211 humans |
| 2 | User Acquisition | — | Right but undefined | — |
| 3 | Never Joined a Game (%) | 49.8% | **Wrong** | **53.8%** |
| 4 | Joined But Never Completed (%) | 16.6% | **Wrong** | **12.5%** |
| 5 | Completed Exactly 1 Game (%) | 16.5% | Right but undefined | 16.7% |
| 6 | Completed 2+ Games (%) | 17.0% | Right but undefined | 17.1% |
| 7 | NMR Rate | 17.13% | Right but undefined | 17.24% human-only |
| 8 | Civil Disorder Exposure — Distribution | 68/19/10/3% | Wrong, immaterial today | one game moves |
| 9 | Player Reliability Tier Distribution | 2684/302/249 | **Wrong** | **3164/31/40** |
| 10 | Civil Disorder: Games with ≥1 CD | 31.9% | Right but redundant | duplicate of #8 |

Two cards move materially under a corrected definition: **Never Joined** (+4.0pp)
and **Player Reliability Tier Distribution** (`Reliable` falls from 302 to 31).

---

## Cross-cutting findings

These apply to more than one card and are the substance of the audit.

### No card excludes bot accounts

Bot users are ordinary `auth_user` rows. Nothing in production code sets
`is_staff` on them — the seed migration `bot_profile/0002_seed_roster.py:200-230`
creates them with `User.objects.get_or_create(...)` and only `is_active` set, so
`is_staff` takes its default of `FALSE`. Verified: 22 non-staff bot accounts, 1
staff account, 3,211 non-staff humans, 3,234 rows total.

`is_staff = FALSE` is therefore **not** a "real user" filter. The only marker of a
bot seat is a related `BotProfile`:

```sql
LEFT JOIN bot_profile_botprofile bp ON bp.user_id = au.id
-- humans:
WHERE bp.id IS NULL
```

Impact is small on user-counting cards (22 of 3,233, 0.7%) and small but
directional on NMR rate, where it is the exact mechanism the map warns about.

### `private` is filtered by no card, though the app filters it

`get_rated_outcomes` (`service/user_profile/commitment.py:44-58`) — the app's own
rated set — excludes `phase__game__private=True`. No dashboard card does. 48 of
the 226 active non-sandbox games are private.

### `last_login` is unusable

`last_login IS NULL` for all 3,235 non-staff users — JWT auth never writes it. No
MAU or activity metric can be built from `auth_user` as it stands. This bears on
the map's open question about whether Users survives and what MAU would mean.

### User deletion is hard deletion, so history is not stable

`Member.user` is `on_delete=SET_NULL`; 166 member rows across 122 games have
`user_id IS NULL`. Deleted accounts leave `auth_user` entirely, so any card
derived from `auth_user` describes *surviving* users. Total Users can go down,
and the acquisition curve silently rewrites its own past.

### `orders_outcome IS NOT NULL` already implies `has_possible_orders`

All 86,862 phase-state rows with a non-null `orders_outcome` have
`has_possible_orders = TRUE`; there are zero counterexamples. This means the NMR
card's omission of `has_possible_orders` is harmless, and — relevant to
[#1141](https://github.com/johnpooch/diplicity-react/issues/1141) — it **confirms
that a seat replaced by a bot drops out of the NMR denominator automatically**,
because the replaced member's subsequent phase states are created with
`has_possible_orders = False` and so never receive an `orders_outcome`.

### The map's "Commitment does not exist yet" is wrong at `9cbb3c9`

Commitment is shipped and populated, not design-only:

- `UserProfile.commitment` is a real field (`user_profile/migrations/0006_userprofile_commitment.py`)
- `score_commitment` and `get_rated_outcomes` are implemented in `service/user_profile/commitment.py`
- it is recomputed on phase resolution (`phase/models.py:_recompute_commitment`)
- `service/user_profile/management/commands/backfill_commitment.py` exists
- `Game.commitment_requirement` ships with migrations `game/0022` and `game/0023`

Production distribution today: `undefined` 2,881 · `high` 194 · `low` 117 ·
`medium` 42. The design doc's feared empty middle tier is real — `medium` is 1.3%
of profiles.

The rated set is likewise already fixed in code: excludes kicked members, sandbox
games and private games; requires `has_possible_orders` and a completed phase;
clamps the run after two consecutive movement NMRs; window of 10.

`docs/reliability/features/commitment-scoring-design-doc.md`, cited by the map and
by [#1145](https://github.com/johnpooch/diplicity-react/issues/1145), does not
exist in this repository or anywhere in its git history.

One concern the Commitment section will inherit: `get_rated_outcomes` orders the
rated window by `state.phase.updated_at` — the column the `metabase` skill flags
as reset by batch operations. Not a dashboard defect, but it means the app's
"last 10 phases" window may not be the last 10 phases.

---

## Card 1 — Total Users

```sql
SELECT COUNT(*) AS total_users
FROM auth_user
WHERE is_staff = FALSE
```

**Measures.** Rows in `auth_user` that are not the single staff account, at query
time. Reads **3,233**.

**Time column and grain.** None — a point-in-time snapshot.

**Exclusions.** Staff only. Does not exclude bot accounts (22), inactive accounts
(`is_active = FALSE`, 66), or accounts that never joined a game.

**Verdict: wrong.** It counts 22 bots as users. The human figure is **3,211**. It
is also a survivor count rather than a signup count (see hard deletion above), so
it is not the running total the name implies.

---

## Card 2 — User Acquisition

```sql
WITH daily AS (
  SELECT date_trunc('day', date_joined) AS day, COUNT(*) AS new_users
  FROM auth_user WHERE is_staff = FALSE GROUP BY 1
), spine AS (
  SELECT generate_series(
    (SELECT MIN(day) FROM daily), date_trunc('day', now()), interval '1 day'
  ) AS day
), cumulative AS (
  SELECT spine.day,
    COALESCE(daily.new_users, 0) AS new_users,
    SUM(COALESCE(daily.new_users, 0)) OVER (ORDER BY spine.day) AS total_users
  FROM spine LEFT JOIN daily USING (day)
)
SELECT * FROM cumulative
WHERE day >= date_trunc('day', now()) - interval '30 days'
ORDER BY day;
```

**Measures.** Daily signups and the running cumulative total, windowed to the last
30 days. 837 signups in the window.

**Time column and grain.** `auth_user.date_joined`, day grain. This is the right
choice — `date_joined` is not one of the trapped columns.

**Exclusions.** Staff only.

**Verdict: right but undefined.** The cumulative arithmetic is correct — it sums
the full history before windowing, so day-1 of the window carries the true
all-time total rather than restarting at zero. Three undeclared properties:

1. **Bots appear as signups.** 9 of the last 30 days' 837. Bot `date_joined` is
   the migration run date (first 2026-06-27, last 2026-07-29), so the roster seeds
   land as artificial step changes on specific days.
2. **The curve rewrites its own past.** Hard deletion removes the row entirely, so
   a point plotted last week can fall this week.
3. **The final bucket is a partial day.** `new_users` for today always undercounts
   and will read as a drop at the right edge of every chart.

---

## Cards 3–6 — the Funnel

All four share one CTE:

```sql
WITH user_counts AS (
    SELECT au.id AS user_id,
        COUNT(DISTINCT mm_any.game_id) AS games_joined,
        COUNT(DISTINCT mm_finished.game_id) AS games_completed
    FROM auth_user au
    LEFT JOIN member_member mm_any ON mm_any.user_id = au.id
    LEFT JOIN member_member mm_finished ON mm_finished.user_id = au.id
        AND mm_finished.game_id IN (
            SELECT id FROM game_game
            WHERE status IN ('completed', 'abandoned') AND sandbox = FALSE
        )
    WHERE au.is_staff = FALSE
    GROUP BY au.id
)
```

then differ only in the `FILTER` clause: `games_joined = 0`,
`games_joined > 0 AND games_completed = 0`, `games_completed = 1`,
`games_completed >= 2`.

**Measures.** A lifetime funnel over every non-staff account ever created. The four
buckets are mutually exclusive and exhaustive, so they sum to 100% by construction.

**Time column and grain.** None. No cohorting and no window — the denominator is
all users ever, so every percentage is dominated by cumulative signup volume and
can only move slowly.

**Exclusions.** Staff. Sandbox on the *completed* leg only.

### The asymmetric sandbox filter

`mm_finished` excludes sandbox games; `mm_any` does not. So a user whose only
membership is a solo sandbox game against bots counts as having "joined a game".
263 users have a sandbox membership across 346 sandbox games.

Measured both ways:

| | As published | Sandbox excluded from `games_joined` |
|---|---|---|
| Never Joined | 49.8% | **53.8%** |
| Joined But Never Completed | 16.6% | **12.5%** |
| Completed Exactly 1 | 16.5% | 16.7% |
| Completed 2+ | 17.0% | 17.1% |

**Card 3 verdict: wrong** — 49.8% understates non-activation by 4.0pp.
**Card 4 verdict: wrong** — the same defect inflates it by 4.1pp.
**Cards 5 and 6 verdicts: right but undefined** — the sandbox asymmetry does not
reach their numerators; excluding bots moves them 0.2pp.

### "Completed" includes abandoned games

`status IN ('completed', 'abandoned')` — 724 completed and 102 abandoned
non-sandbox games. A player whose game collapsed is counted identically to one who
played it out. Defensible as "reached an end state", but the label says completed
and the distinction is precisely what a reliability dashboard is about.

### Correct by luck

The two `LEFT JOIN`s against `member_member` produce a cartesian product per user
(joined × finished rows). `COUNT(DISTINCT ...)` rescues the result, but the query
does far more work than it needs to and any future non-distinct aggregate added to
this CTE will be silently wrong.

---

## Card 7 — NMR Rate

```sql
SELECT ROUND(100.0 * COUNT(*) FILTER (WHERE ps.orders_outcome = 'nmr')
             / NULLIF(COUNT(*), 0), 2) AS nmr_rate_pct
FROM phase_phasestate ps
JOIN phase_phase pp ON ps.phase_id = pp.id
JOIN game_game gg ON pp.game_id = gg.id
WHERE gg.sandbox = FALSE
  AND gg.status != 'abandoned'
  AND ps.orders_outcome IS NOT NULL
  AND pp.scheduled_resolution >= NOW() - INTERVAL '14 days'
  AND pp.scheduled_resolution < NOW()
```

**Measures.** Share of phase-seats that failed to order, over phases whose deadline
fell in the last 14 days. Reads 17.13% on the dashboard; 17.03% on this run
(19,081 rows) — ordinary drift of a rolling window.

**Time column and grain.** `scheduled_resolution`, rolling 14 days. This is the
correct column per the `metabase` skill.

**Exclusions.** Sandbox games, abandoned games, phase-seats with no outcome.
Not excluded: bot seats, private games, kicked members.

### The 17% vs ~30% gap is a window difference

Measured on the card's own definition, varying only the window and the filters:

| Variant | n | NMR |
|---|---|---|
| **Card as written** (14d, non-abandoned, all seats) | 19,081 | **17.03%** |
| 14d, non-abandoned, humans only | 18,849 | 17.24% |
| 14d, + `has_possible_orders` | 18,849 | 17.24% |
| **All-time**, non-abandoned, all seats | 78,690 | **27.03%** |
| All-time, including abandoned games | 81,854 | 27.79% |
| All-time, including abandoned, humans only | 81,344 | 27.96% |

The design doc's ~30% is an all-time figure; the card is a 14-day one. The card is
not definitionally broken — but neither number is labelled with its window, which
is how the two came to be compared in the first place.

### Three undeclared choices

1. **Bot seats are in the denominator** — 232 of 19,081 rows in the window. They
   pull the rate from 17.24% (humans) to 17.03%, so 0.2pp today. Small now, but
   this is the mechanism the map identifies: every seat handed to a bot improves
   the headline without any human behaving differently, and the effect grows with
   `replace_member_with_bot` usage.
2. **Abandoned games are excluded**, which is a survivorship filter on the exact
   population the metric is about — games abandoned are games where people stopped
   ordering. All-time: 27.03% excluding vs 27.79% including.
3. **381 phase-state rows in non-abandoned games have `scheduled_resolution IS
   NULL`** (manual-resolution games) and are invisible to every windowed run of
   this card.

**Verdict: right but undefined.** The number is defensible and the time column is
the right one; the window, the bot seats, the abandoned-game exclusion and the
NULL-deadline drop-through are all unlabelled.

---

## Card 8 — Civil Disorder Exposure — Distribution

```sql
SELECT CASE WHEN cd_count = 0 THEN '0 - Clean'
            WHEN cd_count = 1 THEN '1 - Damaged'
            WHEN cd_count = 2 THEN '2 - Severe'
            ELSE '3+ - Critical' END AS cd_severity,
       COUNT(*) AS game_count,
       ROUND(100.0 * COUNT(*) / NULLIF(SUM(COUNT(*)) OVER (), 0), 1) AS pct_of_active_games
FROM (
    SELECT gg.id,
        COUNT(*) FILTER (WHERE mm.civil_disorder = TRUE AND mm.eliminated = FALSE) AS cd_count
    FROM game_game gg JOIN member_member mm ON mm.game_id = gg.id
    WHERE gg.status = 'active' AND gg.sandbox = FALSE
    GROUP BY gg.id
) game_cd_counts
GROUP BY cd_severity ORDER BY MIN(cd_count)
```

**Measures.** Active non-sandbox games bucketed by how many of their members are
flagged `civil_disorder` and not eliminated. 226 games: Clean 154 (68.1%), Damaged
43 (19.0%), Severe 22 (9.7%), Critical 7 (3.1%).

**Time column and grain.** None — a snapshot of current active games. Being a
snapshot, it cannot show whether CD exposure is improving, which is what the
dashboard exists to answer.

**Exclusions.** Sandbox games, eliminated members. Not excluded: kicked members,
replaced members, private games, bot seats.

### Repaired seats still count as damage

A seat handed to a bot via `replace_member_with_bot` leaves the original member row
in place with `civil_disorder = TRUE` and `kicked = TRUE` — the row is deliberately
kept so its history stays attributable. This card counts it, so a game that has
been *fixed* still reads as damaged, permanently. There are also two member rows
for such a seat, so the game can be double-counted toward a higher severity bucket.

Recomputed with `AND NOT mm.kicked AND mm.replaced_by_id IS NULL`:

| Bucket | As published | Repaired seats excluded |
|---|---|---|
| Clean | 154 | 154 |
| Damaged | 43 | 43 |
| Severe | 22 | 23 |
| Critical | 7 | 6 |

**Verdict: wrong, immaterial today.** Only 14 kicked members sit in active games, so
exactly one game moves and the Clean share is unchanged. The defect is in the
definition, not yet in the number — and it grows with every bot replacement.

`AND mm.eliminated = FALSE` is a reasonable guard but partly redundant:
`phase/models.py:425-434` clears `civil_disorder` when a newly-CD member is
eliminated in the same resolution.

---

## Card 9 — Player Reliability Tier Distribution

```sql
WITH finished AS (
    SELECT mm.user_id, mm.civil_disorder,
        ROW_NUMBER() OVER (PARTITION BY mm.user_id ORDER BY gg.updated_at DESC) AS r,
        COUNT(*) OVER (PARTITION BY mm.user_id) AS total
    FROM member_member mm
    JOIN game_game gg ON mm.game_id = gg.id
    JOIN auth_user au ON mm.user_id = au.id
    WHERE gg.status IN ('completed', 'abandoned')
        AND gg.sandbox = FALSE AND au.is_staff = FALSE
),
last10 AS (
    SELECT user_id, total AS total_finished,
        SUM(CASE WHEN civil_disorder THEN 1 ELSE 0 END) AS cd_count
    FROM finished WHERE r <= 10 GROUP BY user_id, total
),
tiers AS (
    SELECT au.id AS user_id,
        CASE WHEN COALESCE(l.total_finished, 0) < 2 THEN 'New Player'
             WHEN l.cd_count <= 1 THEN 'Reliable'
             ELSE 'Unreliable' END AS tier
    FROM auth_user au LEFT JOIN last10 l ON l.user_id = au.id
    WHERE au.is_staff = FALSE
)
SELECT tier, COUNT(*) AS player_count FROM tiers GROUP BY tier ...
```

**Measures.** Nothing the product defines. Reads New Player 2,684 · Reliable 302 ·
Unreliable 249.

### Where `Unreliable` comes from

The card's own `ELSE` branch, and nowhere else. `get_player_stats`
(`service/user_profile/utils.py:15-68`) returns `"new"`, `"reliable"` or `None`;
`tier_allows_min_reliability` consumes exactly those three. There is no
`Unreliable` tier in the codebase. The card does not report the app's tier — it
invents a parallel tiering that happens to share two labels.

### Every divergence, and every one of them loosens the test

| Axis | App (`get_player_stats`) | Card |
|---|---|---|
| "New" cutoff | `total_games < 10` | `total_finished < 2` |
| Game set | `status = 'completed'` | `completed` **or** `abandoned` |
| Kicked members | excluded (`kicked=False`) | included |
| Ordering of the last-N window | `-game__finished_at` | `gg.updated_at DESC` |
| "Reliable" test | `nmr_rate <= 0.1` **and** `cd_rate <= 0.1` | `cd_count <= 1` only |
| Third bucket | `None` — no tier | `Unreliable` |
| Bot accounts | n/a | included |

Recomputing the app's definition over production — completed non-sandbox games,
`kicked = False`, ordered by `finished_at`, both NMR and CD thresholds applied:

| Tier | App definition | Card |
|---|---|---|
| new / New Player | **3,164** | 2,684 |
| reliable / Reliable | **31** | 302 |
| no tier / Unreliable | **40** | 249 |

The card's `Reliable` bucket is roughly **ten times** the app's. It drops the NMR
half of the test entirely, and `cd_count <= 1` out of as few as two games lets a
player with a 50% civil-disorder rate read as Reliable.

The ordering column is wrong too: `game_game.updated_at` is `auto_now`, so any save
touches it and the "last 10 finished games" window is ordered by last write rather
than by when the games finished. `finished_at` exists and is what the app uses.

**Verdict: wrong.** Not a card to correct — a card whose question needs re-asking
against `UserProfile.commitment`, which now exists and is the signal intended to
replace this one.

---

## Card 10 — Civil Disorder: Games with at least 1 CD

```sql
SELECT ROUND(100.0 * COUNT(*) FILTER (
           WHERE EXISTS (SELECT 1 FROM member_member mm
                         WHERE mm.game_id = gg.id
                           AND mm.civil_disorder = TRUE
                           AND mm.eliminated = FALSE)
       ) / NULLIF(COUNT(*), 0), 1) AS pct_games_with_cd
FROM game_game gg
WHERE gg.status = 'active' AND gg.sandbox = FALSE
```

**Measures.** Share of active non-sandbox games with at least one non-eliminated
CD member. Reads **31.9%**.

**Time column and grain.** None — snapshot, same population as card 8.

**Verdict: right but redundant.** It is arithmetically `100 − pct('0 - Clean')`
from card 8: 100 − 68.1 = 31.9. Identical population, identical filters, identical
kicked/replaced defect — and excluding repaired seats leaves it at 31.9% because
the one game that moves shifts between two non-clean buckets. Two cards, one fact.

---

## What this hands to the next tickets

- **[#1141](https://github.com/johnpooch/diplicity-react/issues/1141) (rated set)** — the mechanism it asks to confirm is confirmed: replaced seats leave the NMR denominator automatically, because `orders_outcome IS NOT NULL` implies `has_possible_orders = TRUE` with zero exceptions in 86,862 rows. It also now has the bot-seat magnitude (0.2pp today), the abandoned-game magnitude (0.76pp all-time), the NULL-deadline count (381 rows), and the fact that the app's own rated set already exists in `service/user_profile/commitment.py` and excludes private games.
- **[#1145](https://github.com/johnpooch/diplicity-react/issues/1145) (Commitment section)** — its premise is falsified. Commitment exists, is populated, and the design doc it cites is not in the repository.
- **[#1146](https://github.com/johnpooch/diplicity-react/issues/1146) (inventory and layout)** — three cards to drop or rebuild (9 as wrong, 10 as duplicate, 3/4 as corrigible), and the observation that cards 8, 9 and 10 are all snapshots on a dashboard whose purpose is showing change over time.
- **Users / Funnel fog** — `last_login` is unwritable, so no MAU exists today without new instrumentation.
