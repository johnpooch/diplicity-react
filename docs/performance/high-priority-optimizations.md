# High-Priority Endpoint Optimizations

Strategies for the top-priority endpoints identified in [overview.md](./overview.md). Each
section states the evidence, the root cause as found in the code, the proposed change, and
how to verify it. File references are to the current state of `main`.

A recurring theme: `Phase.options` (`phase/models.py:877`) is a large per-phase JSON blob
(the full adjudication options tree). It is only ever read for the *current* phase of a game
(via `Phase.transformed_options`), but several query paths fetch it for *every* phase.

---

## 0. Prerequisite: database span instrumentation

Traces currently contain no SQL spans. On `GET games/`, custom app spans account for <0.3% of
request time; the remaining ~99.7% is unattributed. Every fix below changes query shape, so
before starting, enable OpenTelemetry Django database instrumentation (psycopg
instrumentation is already implied by the existing `opentelemetry` usage in the codebase) so
that before/after comparisons attribute time to specific queries.

- **Effort:** small. **Risk:** trace volume growth — sample if needed.

---

## 1. `GET games/`

**Evidence:** 66,492 req/wk, P50 319ms, P95 2,073ms, max 12.1s. This backs the game list —
the app's home screen — so the P95 is felt as a 2-second cold screen.

**Root causes** (`GameListView.get_queryset`, `game/views.py:49`):

1. **All phases fetched with all columns.** `with_list_data()` (`game/models.py:75`) ends
   with `phases_prefetch = Prefetch("phases", queryset=Phase.objects.prefetch_related(...))`
   — no `.only()`/`.defer()`. Every historical phase of every listed game is loaded,
   including each phase's `options` blob. `GameListSerializer` reads only
   `id/ordinal/season/year/type/status/scheduled_resolution` and (for the current phase)
   units/supply centers — never `options`. Cost grows linearly with game age.
2. **Phase states prefetched for every phase.** The serializer needs phase states only for
   the current phase (`order_status`, `phase_confirmed`) and the most recent completed phase
   (`member_status`, `game/serializers.py:208`), but the prefetch annotates and loads them
   for all phases.
3. **Per-game correlated unread-count subquery.** `with_total_unread_counts`
   (`game/models.py:45`) runs a correlated `ChannelMessage` count subquery per game row.
4. **Global `DISTINCT ON` subquery for current-phase ids.** `current_phase_ids`
   (`game/models.py:92`) scans the whole `Phase` table (`DISTINCT ON (game_id)`) inside the
   units/supply-center prefetch, regardless of which 20 games the page contains.

**Strategy** (in order of expected payoff):

1. Add `.defer("options")` to the phase prefetch queryset in `with_list_data()`. No
   serializer change needed; deferred fields lazy-load if ever touched, so this is
   behavior-preserving by construction.
2. Restrict the phase prefetch to slim fields with `.only(...)` matching what the
   serializers read (equivalent to the existing pattern in `PhaseListView`,
   `phase/views.py:89`).
3. Split the phase-states prefetch so it applies only to the current and latest completed
   phase, mirroring how `current_units_prefetch` already scopes units to current phases.
4. Measure again. If the unread-count subquery is still significant (visible once DB spans
   exist), replace it with a single grouped query over the page's game ids executed after
   pagination, stitched in Python.

**Verify:** `service/game/tests` (list endpoint tests), then Honeycomb P50/P95 for
`http.route = games/` week-over-week. Expect the long tail (old games) to collapse; target
P95 under ~500ms.

---

## 2. `GET game/<id>/`

**Evidence:** 410,530 req/wk — the highest-volume route and the #1 consumer of total server
time (47M ms/wk). P50 63ms is acceptable; P95 267ms and max 9.2s are driven by long games.

**Root cause** (`GameRetrieveView`, `game/views.py:32`): `with_retrieve_data()`
(`game/models.py:122`) prefetches *all* phases with *all* columns (including `options`) and
all their phase states with an `order_count` annotation. `GameRetrieveSerializer` reads only
phase ids (`get_phases`), the current phase id, and phase states of the current and latest
completed phases. Additionally `get_total_unread_message_count`
(`game/serializers.py:275`) issues its own correlated query per request instead of using the
queryset annotation that already exists for the list path.

**Strategy:**

1. `.defer("options")` / `.only(...)` on the phases prefetch, exactly as in §1.
2. Scope the phase-states prefetch to the current + latest completed phase.
3. Reuse `with_total_unread_counts(user)` on the retrieve queryset (it is already written as
   a queryset method) and change the serializer field to read the annotation, replacing the
   hand-rolled per-request query. Requires plumbing `request.user` into `get_object`
   (`game/views.py:38`), where the user is already available.

Because of the extreme volume, even a 20–30ms P50 reduction here saves more aggregate server
time than eliminating most other endpoints entirely.

**Verify:** `service/game/tests` retrieve tests; Honeycomb `SUM(duration_ms)` for the route —
this is the metric to watch, more than P50.

---

## 3. `Game.current_phase` — `orders/` POST, `options/` GET, `confirm-phase` PATCH

**Evidence:** `POST game/<id>/orders/` — 50,588 req/wk, P95 666ms, max 25.6s.
`GET game/<id>/options/` — 64,206 req/wk, P95 664ms. `PATCH confirm-phase` — 4,374 req/wk,
P95 483ms. These are the core order-submission gameplay loop; the maxes mean players
occasionally wait tens of seconds to submit a move.

**Root cause:** these views use `CurrentPhaseMixin` (`common/views.py:69`), which calls
`resolve_game()` (a bare `Game` fetch — fine) and then `game.current_phase`. The
`current_phase` property (`game/models.py:443`) has no prefetch on this path, so it executes
`list(self.phases.all())` — loading **every phase of the game, with every column, including
every historical `options` blob** — to return the last element. A three-year-old game with
100+ phases loads 100+ large JSON documents to serve a single order POST. This is the
clearest linear-degradation bug in the codebase, and one fix covers three top-ten endpoints.

**Strategy:**

1. Change the non-prefetched fallback in `Game.current_phase` to fetch one row:
   `self.phases.order_by("ordinal").last()`. The prefetched fast path
   (`active_phases_list`) stays as is. This alone reduces the fetch from O(phases) to O(1);
   the one fetched row legitimately includes `options`, which `OrderOptionsView`
   (`order/views.py:34`) and order validation genuinely need.
2. Audit other callers of `current_phase` that reach it without prefetch (e.g.
   `PhaseStateUpdateView.get_object`, `phase/views.py:35`) — they inherit the fix
   automatically since it's the shared property.
3. Longer term (only if still needed once measured): denormalize a `Game.current_phase`
   foreign key maintained at phase creation/resolution, eliminating the sort entirely.

**Verify:** `service/order/tests` and `service/phase/tests`; Honeycomb P95 for
`game/<str:game_id>/orders/` POST and `game/<str:game_id>/options/` GET. Expect the P95s to
drop toward their P50s and the multi-second maxes to disappear.

---

## 4. `GET variants/`

**Evidence:** 14,821 req/wk, P50 806ms, P95 1,649ms. The worst P50 of any user-facing route
with real traffic; it is fetched on app start, so it delays first paint of anything
variant-dependent.

**Root cause** (`VariantListCreateView`, `variant/views.py:49`): every non-304 response
serializes the full board definition for every visible variant — provinces with parents and
named coasts, nations with flags, and the template phase's units and supply centers
(`with_related_data()`, `variant/models.py:45`). An ETag exists (`_variants_list_etag`,
`variant/views.py:35`), but a P50 of 806ms shows the majority of requests still pay the full
build — the 304 path would return in milliseconds. The ETag also hashes `user.id`, which
needlessly fragments what is (per user-visible content) mostly a shared payload: the only
user-dependent inputs are colorblind mode and draft/member visibility.

**Strategy:**

1. **Find out why the ETag isn't hitting.** Check whether the web/mobile clients send
   `If-None-Match` (RTK Query does not by default unless the browser HTTP cache is allowed
   to — `Cache-Control: private, no-cache` permits revalidation, so browsers should; the
   Capacitor apps may not). This is cheap to confirm from Honeycomb by adding a span
   attribute for the request header, and may be a client-side fix.
2. **Server-side render cache.** Cache the serialized variant list keyed by
   `(variant_max_updated, flag_max_updated, colorblind_mode)` — the same inputs as the ETag
   minus `user.id` — and serve the cached JSON for the common published-variants case
   (anonymous users and users with no drafts/memberships get byte-identical payloads).
   Variants change rarely (`updated_at` max is already queried per request), so hit rates
   will be near 100%.
3. **Longer term:** split the heavy board data out of the list into a per-variant resource
   addressed by content hash, following the existing immutable-URL pattern of
   `VariantSvgView` (`variant/views.py:133`) which already serves with
   `Cache-Control: immutable`. The list then becomes lightweight metadata.

**Verify:** `service/variant/tests`; Honeycomb P50 for `variants/` GET — target is tens of
milliseconds for cache hits, not hundreds.

---

## 5. `POST phase/deadline-warnings/`

**Evidence:** 3,056 req/wk (a scheduler hitting it roughly every 3 minutes), P50 1,544ms,
P95 2,364ms, max 10.4s. Not user-facing, but it occupies a worker for 1.5–2.4s on every tick
— ~82 minutes of server time per week — and its cost grows with the number of active games.

**Root cause** (`send_deadline_warnings`, `phase/models.py:262`): the query loads **every
active phase in the system** with heavy prefetches — all phase states with members, users,
nations and *orders*, plus units and supply centers — and only then filters in Python by
`time_until_deadline`. The largest warning threshold is 14,400s (4 hours), so any phase whose
deadline is further out than 4 hours (the vast majority, given 24h+ phase durations) is
fetched, hydrated, and discarded.

**Strategy:**

1. Add a SQL window filter to the initial query:
   `scheduled_resolution__gt=now, scheduled_resolution__lte=now + timedelta(seconds=14400)`.
   This is a pure superset of the Python-side threshold check (which stays as the precise
   per-game filter), so behavior is unchanged while the candidate set shrinks from "all
   active phases" to "phases within 4 hours of deadline".
2. Two-step fetch: run the window query with no prefetches to get candidate ids, then
   re-fetch only candidates with the heavy prefetches. With step 1 alone this may already be
   unnecessary — measure first.
3. Add an index on `(status, scheduled_resolution)` for `Phase` if the DB spans show the
   window scan is slow (a `status` index does not currently exist on `Phase`; only `Game`
   has one).

**Verify:** `service/phase/test_deadline_reminders.py`; Honeycomb P50 for the route. Expect
sub-200ms ticks outside the warning windows.

---

## 6. `GET game/<id>/orders/<phase_id>`

**Evidence:** 96,087 req/wk, P50 48ms, P95 835ms, max 28.5s. The P50 is healthy; the tail is
the problem, and a 28.5s max points at pathological cases rather than uniform slowness.

**Root causes** (`OrderListView`, `order/views.py:13`):

1. `SelectedPhaseMixin.get_phase` → `resolve_phase` (`common/views.py:24`) does
   `get_object_or_404(Phase, ...)` with all columns — including the `options` blob — even
   though this view never reads options. One row, but a large one, on every request.
2. For **completed** phases, `visible_to_user_in_phase` (`order/models.py:16`) returns every
   nation's orders, each hydrated through a very wide `select_related`/`prefetch_related`
   graph (`with_related_data()`, `order/models.py:25`), then post-processed by
   `build_move_coast_lookup`. Late-game adjustment/movement phases with many orders explain
   the tail.
3. Completed-phase responses are **immutable** — orders on a resolved phase never change —
   yet every request rebuilds them.

**Strategy:**

1. Defer `options` in `resolve_phase` (`.defer("options")` on the lookup) — shared win for
   every `SelectedPhaseMixin` view.
2. Cache completed-phase order lists. The cleanest fit with existing patterns is HTTP
   caching, as done for variant SVGs: when `phase.status == completed`, respond with
   `Cache-Control: private, max-age=<long>` plus an ETag derived from the phase id (content
   is immutable once resolved; visibility for completed phases is not user-specific, per
   `visible_to_user_in_phase`). A server-side render cache keyed by phase id achieves the
   same without trusting client caches.
3. Pull a few >10s traces from Honeycomb once DB spans exist to confirm the tail is the
   completed-phase fan-out and not lock contention from concurrent phase resolution.

**Verify:** `service/order/tests`; Honeycomb P95/max for the route. Expect P95 to approach
P50 once completed phases are cached.

---

## Sequencing

1. §0 instrumentation, then §3 (`current_phase`) — smallest diff, three endpoints improved.
2. §1 + §2 together (same queryset methods, same defer pattern, one PR).
3. §5 (self-contained, low risk).
4. §4 and §6 (both introduce caching, which deserves its own review round).

Each step is independently shippable and verifiable against the Honeycomb baselines recorded
in [overview.md](./overview.md).
