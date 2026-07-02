# Endpoint Performance: Overview

This document ranks production API endpoints by optimization priority, based on seven days of
Honeycomb data (2026-06-25 to 2026-07-02, ~1.13M requests). A companion document,
[high-priority-optimizations.md](./high-priority-optimizations.md), describes the concrete
optimization strategy for each of the top-priority endpoints.

## Method

Latency percentiles alone are a misleading way to prioritize: several of the slowest routes by
P50 serve a handful of requests per week, while the routes that dominate real user experience
did not appear in the original latency-sorted view at all. This analysis therefore combines
three signals from Honeycomb:

1. **Request volume** — how many users feel the latency.
2. **Latency (P50 / P95 / max)** — how bad it feels when they do.
3. **Total server time (SUM of duration_ms)** — aggregate cost, a proxy for infrastructure
   load and a tie-breaker between endpoints.

## The seven-day picture

Top routes by total server time (root HTTP spans, `duration_ms`):

| Route | Method | Requests | P50 (ms) | P95 (ms) | Max (ms) | Total time (min) |
|---|---|---:|---:|---:|---:|---:|
| `game/<id>/` | GET | 410,530 | 63 | 267 | 9,241 | 785 |
| `games/` | GET | 66,492 | 319 | 2,073 | 12,078 | 708 |
| `game/<id>/orders/<phase_id>` | GET | 96,087 | 48 | 835 | 28,509 | 330 |
| `variants/` | GET | 14,821 | 806 | 1,649 | 10,412 | 219 |
| `game/<id>/phase/<phase_id>/` | GET | 102,560 | 89 | 193 | 9,929 | 191 |
| `game/<id>/phase-states/` | GET | 106,644 | 59 | 262 | 7,582 | 186 |
| `game/<id>/orders/` | POST | 50,588 | 111 | 666 | 25,641 | 145 |
| `game/<id>/options/` | GET | 64,206 | 54 | 664 | 8,235 | 139 |
| `games/<id>/channels/` | GET | 71,105 | 84 | 301 | 7,654 | 131 |
| `phase/deadline-warnings/` | POST | 3,056 | 1,544 | 2,364 | 10,446 | 82 |
| `game/<id>/resolve-phase/` | POST | 1,843 | 490 | 1,247 | 5,145 | 18 |
| `game/<id>/clone-to-sandbox/` | POST | 198 | 744 | 3,536 | 29,961 | 5 |
| `auth/register/` | POST | 83 | 685 | 945 | 967 | <1 |
| `auth/apple-login/` | POST | 51 | 695 | 859 | 1,302 | <1 |

Two observations reframe the original data:

- **The busiest endpoints were missing from the latency-sorted view.** `game/<id>/` alone is
  410k requests/week and is the single largest consumer of server time, despite a modest P50.
- **Several "slow" endpoints are near-idle.** `admin/variant/.../replace-files/` (2 requests),
  `variants/<pk>/` PUT (1 request), `variants/<id>/dvar/` (3 requests),
  `game/<id>/unpause|pause|extend-deadline|recover-from-civil-disorder` (5–12 requests each)
  are not worth optimizing at all right now.

## A shared root cause

Code inspection of the top offenders points at one dominant pattern: **`Phase.options` — a
large adjudication-options JSON blob (`phase/models.py:877`) — is fetched from the database on
paths that never read it, for every phase of a game rather than just the current one.**

- `GameQuerySet.with_list_data()` and `with_retrieve_data()` (`game/models.py:75,122`)
  prefetch *all* phases of each game with *all* columns. The list and retrieve serializers
  only read phase ids, ordinals, seasons, statuses and phase states — never `options`.
- `Game.current_phase` (`game/models.py:443`) falls back to `list(self.phases.all())`,
  loading every phase of the game — including every historical `options` blob — to return
  the last one. This runs on every request that goes through `CurrentPhaseMixin`
  (`common/views.py:69`): order creation, order options, phase-state confirm, etc.

Because games accumulate phases over time, all of these endpoints degrade linearly with game
age. This is consistent with the observed latency shape: healthy P50s (young games) with long
tails (old games) on `games/`, `orders/` POST, and `options/`.

A secondary systemic finding: **no database spans exist in the traces** — custom app spans
account for under 0.3% of request time on `games/`, and the rest is unattributed (SQL + DRF
serialization). Enabling OpenTelemetry Django/psycopg instrumentation should be part of this
work so each fix can be verified in production.

## Priority ranking

| Priority | Endpoint | Why | Strategy doc |
|---|---|---|---|
| **1** | `GET games/` | Worst high-volume user latency (P95 2.1s on the game-list screen); #2 total server time | [§1](./high-priority-optimizations.md#1-get-games) |
| **2** | `GET game/<id>/` | #1 total server time (410k req/wk); same phases/options over-fetch | [§2](./high-priority-optimizations.md#2-get-gameid) |
| **3** | `Game.current_phase` write/read paths (`orders/` POST, `options/` GET, `confirm-phase` PATCH) | Core gameplay actions with 600ms+ P95s and 25s maxes; single shared fix | [§3](./high-priority-optimizations.md#3-gamecurrent_phase--orders-post-options-get-confirm-phase) |
| **4** | `GET variants/` | Worst P50 (806ms) of any real-traffic user-facing route; loaded on app start | [§4](./high-priority-optimizations.md#4-get-variants) |
| **5** | `POST phase/deadline-warnings/` | Cron every ~3 min at P50 1.5s; loads all active phases then discards most in Python | [§5](./high-priority-optimizations.md#5-post-phasedeadline-warnings) |
| **6** | `GET game/<id>/orders/<phase_id>` | P95 835ms / max 28.5s; completed-phase responses are immutable and cacheable | [§6](./high-priority-optimizations.md#6-get-gameidordersphase_id) |

## Deliberately deprioritized

| Endpoint | Data | Reason |
|---|---|---|
| `POST game/<id>/clone-to-sandbox/` | 198 req/wk, P95 3.5s | Inherently heavy (cascade delete of oldest sandbox + full clone + adjudication start + full re-fetch). Low volume; revisit only if usage grows. |
| `POST game/<id>/resolve-phase/` | 1,843 req/wk, P50 490ms | Dominated by the external adjudication call; sandbox-only. |
| `POST auth/register/`, `auth/login/`, `auth/apple-login/` | ≤238 req/wk, P50 260–710ms | Password hashing is intentionally slow (security); Apple login includes Apple JWKS fetch — caching the JWKS is the only cheap win, worth ~a few hundred ms on 51 req/wk. |
| `POST sandbox-game/`, `POST game/` | ~100–160 req/wk | Game creation copies template units/SCs; acceptable at volume. |
| `variants/<pk>/` PUT, `variants/` POST, `admin/*`, `dvar/`, `pause/`, `unpause/`, `extend-deadline/`, `recover-from-civil-disorder/`, `draw-proposals/.../vote/` | 1–92 req/wk | Volume too low for any optimization to matter. |

## Verification plan

For each change: run the relevant pytest suite, then confirm in Honeycomb after deploy by
re-running the seven-day query (`P50`/`P95`/`SUM(duration_ms)` grouped by `http.route`) and
comparing against the baselines in this document. Enable DB span instrumentation first so
before/after attribution is possible.
