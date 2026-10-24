# Player commitment & scoring: current state

**Snapshot taken 2026-10-24 against `main` at `e6a549f`.** This describes what the code does and what production data shows today. It does not propose changes. It is written so an agent with no prior context can read it, check the cited code, and propose alternatives.

Every claim about the code cites `path:line`. Each production figure comes from a read-only query against production, run on 2026-10-24; the SQL is in [Appendix B](#appendix-b-production-queries). Anything inferred or not checked is marked **(unverified)**.

---

## 1. Summary

- Every player has one stored ordinal, `UserProfile.commitment` ∈ {`high`, `medium`, `low`, `undefined`}. The UI labels `undefined` as "New". It is recomputed whenever a public, non-sandbox phase the player had orders in resolves.
- The score is the NMR share over the player's **10 most recent rated phases**, pooled across all their public games. A rated phase is one where the player had possible orders. There is no time decay and no weighting by game context. A civil-disorder episode is capped at the NMRs that triggered it, usually 2.
- `low` is assigned as soon as ≥2 of the rated phases are NMRs and they make up ≥50% of them, even before 10 phases. `high` and `medium` need the full 10.
- **Gating.** A `low` player cannot join, take over a seat in, or create any public game. Games can be `open` or `committed`; `committed` admits `high` only. Private games are exempt from the `low` lock and from scoring.
- **Display.** The tier shows on the player profile screen and as lock states on game cards. It is not shown in lobbies or player lists, even though the API sends it per member. No notification tells a player their tier changed or why.
- **A second, older system still runs alongside it.** `get_player_stats` computes `reliability_tier` and the NMR rate shown on the profile, using a different population: last 10 completed games, private games included, any phase type. The legacy `Game.min_reliability` column is still written and still drives one UI message.
- **Not built:** forgiveness, the concurrent-active-game cap, and an automatic bot backfill path. Nothing preserves the score across account deletion.
- **Structural findings** (detail in §9):
  1. `low` is effectively permanent. Every route back to rated play is closed to a `low` player.
  2. Being removed by the admin, or having a civil-disorder seat taken over, erases that game's entire history from the player's score.
  3. Withdrawal is penalty-free, as intended.
  4. An NMR counts the same in phase 1 as in phase 40 of a game everyone else has already left.

---

## 2. Where this came from

The reliability epic is not in the repo. Issue #1145 notes that the design doc it referenced, `docs/reliability/features/commitment-scoring-design-doc.md`, "does not exist in this repository or anywhere in its git history". These are the parts of the epic that bear on commitment, condensed from the copy the owner supplied.

**Goal.** Cut the per-phase NMR rate from a ~30% all-time baseline to under 5%. NMR rate is the share of resolved phases where the seat had possible orders and submitted none. The working theory: the problem is "a distinct population of abandoners who poison games", not a broad tail of slightly flaky players, and one civil-disorder (CD) player emits an NMR every movement phase until eliminated.

**§2 Commitment scoring & display.** Replace `reliable`/`new`, which was computed per completed game and is blind to serial abandoners, with one per-phase `commitment` attribute: the share of phases where the player had possible orders and submitted them. Store it as `high > medium > low`, plus `undefined` for a player with too few rated phases. Use a sliding window of the last N rated order-phases with no time decay. Show it on the profile and pre-game lobby with tap-to-explain, not prominently during play. Private games do not contribute. *Strong opinion:* measurement must catch abandoners inside their first game.

**§6 Withdrawal.** Withdrawing at any stage must not harm commitment.

**§7 Mustering.** Players confirm readiness before start, and unconfirmed seats are removed. "Unwillingness to confirm during mustering is a clear signal of a flaky player". The epic does not say whether that signal should affect the score.

**§8 Concurrent-active-game cap.** Applied when a game enters mustering, public games only: high unlimited, medium 3, undefined 1, low 1.

**§11 Commitment gating.** Two creator options: Open (undefined, medium, high) and Committed (high only). No game admits `low`: it is a global lockout from human games. A `low` player recovers by playing against bots or through Forgiveness. Locked games stay visible, with helper text.

**§12 Forgiveness.** A `low` player submits a short reason. The first request within a window (e.g. three months) is auto-accepted and resets the score. Repeat requests go to moderators.

**Feature status as of this snapshot:**

| Epic feature | Status | Evidence |
| --- | --- | --- |
| §1 Notifications re-architecture | Done | Owner's statement |
| §2 Commitment scoring & display | Shipped; owner considers it weak | §4–§7 below |
| §3 Bot opponents | In progress; bot games limited to an email allowlist | `service/user_profile/utils.py:129`, `service/project/settings.py:267` |
| §4 Bot backfill | Not automatic. Seats go to bots only through a management command | `service/agent/management/commands/replace_member_with_bot.py` is the only non-test, non-seed caller of `hand_over_seat` besides the human takeover serializer (`service/member/serializers.py:296`) |
| §5 Takeover link | Shipped (`take_over` / `share_replacement_link` actions, `MemberReplaceView`) | `service/member/models.py:307-327`, `service/member/views.py:108` |
| §6 Withdrawal | Shipped | `service/member/models.py:124` |
| §7 Mustering | Code present; **0 production games have ever mustered** | Appendix B, query E |
| §8 Concurrent cap | Not built (no matching code found by grep) | — |
| §9, §10, §13 | Not assessed for this document | — |
| §11 Gating | Shipped, with a private-game exemption | §6 below |
| §12 Forgiveness | Not built (`forgiv` matches nothing in `service/` or `packages/web/src/`) | — |

**Related issues worth reading:**
- #329: Stats, Scoring & Reliability, the original umbrella.
- #758: surface the tier explanation.
- #1141: settles the dashboard's "rated set". Its resolution comment is the most rigorous write-up of the denominators so far and deliberately diverges from scoring.
- #1145: production tier distribution in August; flags the empty `medium` band.
- #1177: low rating only blocks creation at submit.
- #1186: preserve the rating across account deletion.
- #1194: relax the join lock for private games.

---

## 3. Data model

| Field | Meaning | Where |
| --- | --- | --- |
| `PhaseState.has_possible_orders` | The seat could order in this phase | `service/phase/models.py:979-994` |
| `PhaseState.orders_outcome` | `received` / `nmr` / `NULL` (not rated). Written once at resolution | `service/phase/models.py:980-992` |
| `Member.civil_disorder_at`, `removed_at`, `withdrawn_at`, `eliminated_at` | Departure timestamps, never cleared. The one exception: CD is cleared if elimination lands in the same resolution | `service/member/models.py:178-181`; rules in `.claude/rules/backend/models.md` |
| `Member.replaced_by` | Points to the member who took the seat | `service/member/models.py:182` |
| `Member.nmr_extensions_remaining`, `Game.nmr_extensions_allowed` | Per-game NMR extension budget (0–2) | `service/member/models.py:175`, `service/game/serializers.py:574` |
| `UserProfile.commitment` | Stored tier. Default `undefined` | `service/user_profile/models.py:40-44`, constants `service/common/constants.py:173-184` |
| `UserProfile.kind` | `human` / `llm` / `dumbbot` | `service/user_profile/models.py:45` |
| `Game.commitment_requirement` | `open` / `committed` | `service/game/models.py:674`, `service/common/constants.py:211` |
| `Game.min_reliability` | **Legacy**: `open` / `reliable_and_new` / `reliable_only` | `service/game/models.py:669`, `service/common/constants.py:161` |

Nothing stores tier history, per-phase scoring weights, forgiveness requests, or the score of a deleted account.

---

## 4. How a phase outcome is recorded

`PhaseManager._set_orders_outcome` (`service/phase/models.py:334-358`) runs at the start of every resolution. It rates every phase state with `has_possible_orders=True`, **except** these:

- nations with forced orders in an adjustment phase, i.e. units but no supply centres (`:337-339`, `:878-893`)
- members that are removed, replaced or withdrawn (`:340-345`)

A rated state is `received` if it has **at least one order**, or if the player confirmed orders and is not in CD (`:347`). Otherwise it is `nmr`. Consequences:

- One order out of many counts as fully received.
- Confirming with zero orders counts as received.
- A CD seat whose units hold automatically still records `nmr` every phase until replaced or eliminated.

**NMR extensions.** If a member with extensions left would NMR, the deadline is pushed back and one extension is used instead of resolving (`service/phase/models.py:225-262`). That NMR is never recorded. Extensions are a game-creator option and default to 0.

---

## 5. Civil disorder

`_check_civil_disorder` (`service/phase/models.py:360-412`) runs on **movement** phases of non-sandbox games only. A member who NMRs this movement phase and also NMR'd their previous movement phase in this game enters CD (`civil_disorder_at` is set). Retreat and adjustment NMRs never trigger CD.

What follows:

- The seat becomes `vacant` and is offered for takeover. CD is permanent for that player.
- If the member was admin, admin passes to someone else (`:409-410`).
- Pushes go out: `entered_civil_disorder` to the player and `civil_disorder` to the game (`service/notification/registry.py:328-334`, `:367-380`). Neither mentions commitment.
- The player is **deleted from every pending or mustering game they did not create** and notified (`service/phase/models.py:466-500`). This is an implicit sanction that exists separately from the score.

If every remaining non-eliminated player seat is vacant, the game is abandoned (`Game.should_abandon`, `service/game/models.py:999-1007`).

---

## 6. How the score is computed

All in `service/user_profile/commitment.py`.

### 6.1 Rated set (`get_rated_outcomes`, `:46-76`)

A phase state counts if all of these hold:

- the user's member had `has_possible_orders`
- `orders_outcome` is not NULL
- the phase is completed
- the game is **not sandbox** and **not private** (`:49-55`)

It is **excluded** if the member was removed or replaced and did not withdraw (`:56-59`). Concretely:

| Member history | Effect on rated set |
| --- | --- |
| Played normally | All phases rated |
| Withdrew | Phases before withdrawal rated; the withdrawal phase onward is NULL, so unrated. Test: `service/user_profile/tests.py`, `test_withdrawn_member_keeps_outcomes_from_before_the_seat_was_taken_over` |
| Entered CD, seat never taken | Rated up to the CD trigger (clamp, below) |
| **Entered CD, then someone took the seat** | **Entire game excluded**: `replaced_by` is set and `withdrawn_at` is NULL |
| **Removed by admin in an active game** | **Entire game excluded** |
| Removed at mustering deadline | Entire game excluded. Mustering removes the member after `start()` (`service/game/models.py:504-507`), so `removed_at` is set |
| Deleted their account | Profile is cascade-deleted (see §8.6) |

**CD clamp** (`clamp_post_civil_disorder`, `:30-43`). Each member's states are walked in phase order. Rating stops at the state where the second consecutive **movement** NMR occurs, so one CD contributes the NMRs that caused it, typically 2, plus any retreat or adjustment NMRs between them. Test: `[RECEIVED, NMR×7]` rates as `[NMR, NMR, RECEIVED]`.

**Ordering.** States from all games are pooled and sorted newest-first by `(phase.updated_at, phase.ordinal, id)` (`:72-75`). The team's prod-query notes call `phase_phase.updated_at` "unreliable" for time bucketing. Whether that affects this ordering in practice is **(unverified)**.

### 6.2 Scoring (`score_commitment`, `:13-27`)

Take the first 10 outcomes, where `COMMITMENT_PHASE_WINDOW = 10` (`:6`).

| Condition, evaluated in order | Tier |
| --- | --- |
| No rated outcomes | `undefined` |
| NMR rate ≥ 50% **and** NMR count ≥ 2 | `low` (applies even with fewer than 10 outcomes) |
| Fewer than 10 outcomes | `undefined` |
| NMR rate ≤ 10%, i.e. 0–1 NMR in 10 | `high` |
| Otherwise: 2–4 NMRs in 10 | `medium` |

Worked cases from `service/user_profile/tests.py:1219-1235`:

- `[NMR, NMR]` → `low`. A player who disappears in their first game is `low` after two phases.
- `[RECEIVED×9]` → `undefined`.
- `[NMR + RECEIVED×9]` → `high`.
- `[NMR×2 + RECEIVED×8]` → `medium`. One CD episode alone drops a `high` player to `medium`.
- `[NMR×5 + RECEIVED×5]` → `low`.

### 6.3 When it is recomputed

`PhaseManager._recompute_commitment` (`service/phase/models.py:435-451`) is called from `_resolve_claimed` (`:547-567`), on both the abandon path and the normal path. It recomputes for every user with `has_possible_orders` in the resolved phase, and skips sandbox and private games entirely.

Nothing else triggers a recompute. Seat takeover, admin removal, withdrawal and account restore do not. A change to the rated set from those events, such as a CD vanishing when the seat is taken over, only shows up when that user next has a public phase resolve.

`python manage.py backfill_commitment` recomputes every profile (`service/user_profile/management/commands/backfill_commitment.py`).

Bots also get scores (they have phase states). Nothing reads a bot's score.

---

## 7. How the score is used

### 7.1 Gating rule

`commitment_allows_requirement` (`service/user_profile/commitment.py:86-91`):

- `low` fails in any **public** game.
- `committed` requires `high`, in public **or** private games.
- Everything else passes.

`Game.commitment_eligibility` (`service/game/models.py:844-855`) returns the same decision as `eligible` / `low_locked` / `committed_locked` for the UI.

| Action | Enforcement |
| --- | --- |
| Join a pending game | `MeetsCommitmentRequirement` on `MemberJoinView` (`service/member/views.py:28`; permission at `service/common/permissions.py:166-175`) |
| Take over a vacant seat | Same permission on `MemberReplaceView` (`service/member/views.py:108-117`). The `take_over` action is shown with `blocked_reason=commitment_too_low` (`service/member/models.py:314-324`) |
| Create a public game | Rejected for `low` creators (`service/game/serializers.py:630-636`) |
| Create a `committed` game | Creator must be `high` (`service/game/serializers.py:637-643`). This rule is not in the epic |
| Find Games filter | `eligible_only` exists (`service/game/filters.py:44-52`), but the web client deliberately does not send it (`packages/web/src/screens/Home/FindGames.test.tsx:165-170`). Locked games stay visible, as the epic asks |
| Concurrent-game cap | Not built |

`Game.can_join` (`service/game/models.py:833-842`) does **not** consider commitment. So `canJoin` is `true` for a locked player, and each client screen must check `commitmentEligibility` separately.

### 7.2 Who is locked out, and the way back

A `low` player cannot join, take over or create a public game. Private games are exempt from the lock but also excluded from scoring (§6.1). Bot games need an email allowlist (`service/user_profile/utils.py:129-132`), and would have to be public to count, which a `low` player cannot create.

**The only events that can move a `low` score are phases in public games the player was already seated in when they dropped**, or deleting the account (§8.6). Once those games end, `low` is permanent. This follows from reading the code; no test asserts it.

---

## 8. What players see

### 8.1 Player profile (`packages/web/src/components/PlayerProfileContent.tsx`)

The profile screen is reached at `player/:userId` from Home and from inside a game (`packages/web/src/Router.tsx:224`, `:368`). It has a **Commitment** card with two rows:

- **Tier.** `profile.commitment`, with a popover: "How consistently this player submits orders, based on their last 10 rated phases" (`:20-31`). The "New" popover says a rating appears after 10 rated phases. That is not quite true: `low` can appear after 2.
- **NMR rate.** `profile.nmrRate`, with a popover: "The percentage of movement phases where this player submitted no orders, based on their last 10 games." (`:143-147`). The figure comes from the **legacy** `get_player_stats` (§8.5), which:
  - counts **all phase types**, not just movement
  - counts **completed games only**, so abandoned games are ignored and a player with no finished game shows 0%
  - includes **private** games

  The two rows on one card are computed over different populations and can contradict each other, e.g. Tier `low` next to NMR rate `0%`.

It also has a **Games** card: total games, solo wins, draws, losses. Losses = total − wins − draws, so every non-win, non-draw counts as a loss, withdrawals included (test `test_withdrawn_game_counts_as_a_loss_and_skips_unrated_phases`, `service/user_profile/tests.py:1082`).

The profile does not show:

- how many rated phases the player has, or how close they are to a boundary
- which events counted
- how to improve or recover
- any history

The Account screen does not mention commitment (grep).

### 8.2 Game card in Find Games / My Games (`packages/web/src/components/GameCard.tsx:145-160`, `:417-451`)

- A pending `committed` game shows a "Committed" badge.
- If the viewer is locked, the Join button becomes a disabled lock with "Locked: your commitment is Low" or "Locked: requires High commitment", plus a popover:
  - Low: "...you can't join games right now. Your rating is based on your last 10 rated phases."
  - Committed: "Submit orders on time in your games to raise your rating."
- No recovery path is offered, because none exists (§7.2).

### 8.3 Game Info screen (`packages/web/src/screens/Home/GameInfo.tsx:104-148`)

- Shows **Join game** whenever `game.canJoin` is true, which ignores commitment. A locked player therefore sees an active button and gets a 403: "Your commitment rating does not meet this game's requirement."
- The fallback message "Your reliability is too low to join this game" is keyed on the **legacy** `game.minReliability !== "open"` (`:139-147`).
- The game-info details list shows "High commitment players" for `committed` games (`packages/web/src/components/GameInfoContent.tsx:90-97`).

### 8.4 Elsewhere

- **Create Game.** The "Committed" option is disabled unless the creator is `high`, with helper text (`packages/web/src/screens/Home/CreateGame.tsx:938-946`). There is no client-side handling of a `low` creator choosing a public game; it fails at submit (cf. #1177).
- **Withdraw confirmation:** "Your commitment rating is not affected." (`packages/web/src/components/WithdrawGameAction.tsx:25`).
- **Player lists / lobby.** `MemberSerializer` sends a per-member `commitment`, masked in anonymous games (`service/member/serializers.py:82-88`), but nothing in `packages/web/src` displays it. The epic's "show in the pre-game lobby" is not met.
- **Notifications.** None about tier changes, entering `low`, or being locked out.

### 8.5 The legacy system still running

`get_player_stats` (`service/user_profile/utils.py:73-126`) computes `total_games`, wins, draws, losses, `nmr_rate`, `cd_rate` and `reliability_tier` (`new` / `reliable` / `None`). It works over the last 10 **completed** games (`RELIABILITY_GAME_WINDOW`, `:16`). It runs on **every** request to both profile serializers (`service/user_profile/serializers.py:28-32`, `:68-72`).

- `reliability_tier` is still on the wire, but nothing in `packages/web/src` reads it.
- `Game.min_reliability` is still a column and is still accepted by the create serializer (`service/game/serializers.py:584-587`).
- `MeetsReliabilityRequirement` (`service/common/permissions.py:153-163`) is defined but attached to no view.
- Migration `game/0023` copied `reliable_only` to `committed`.

This is the dormant scaffolding that the project rules (`CLAUDE.md`, "Absent beats dormant scaffolding") say should be removed.

### 8.6 Account deletion

`UserAccountDeleteView.perform_destroy` (`service/user_profile/views.py:105-125`) marks active seats removed and deletes the user, and the profile cascades with it. Nothing records the old score, so re-registering with the same email starts at `undefined`. Issue #1186 proposed storing the score against an email hash and is closed. Its PR (#1198) shows as closed, and no such code exists on `main`. This is a reset button for `low`.

---

## 9. Known problems

The owner raised the first five. The rest came out of writing this document.

1. **How commitment is determined is not clear to players.** §8.1 to §8.4: no count of rated phases, no list of what counted, two contradictory numbers on one card, a "New" explanation that is wrong for `low`, no notifications, a Join button that 403s.
2. **The statistics page is not very useful.** The profile is a tier, a legacy NMR rate, and win/draw/loss counts where withdrawals count as losses (§8.1).
3. **The scoring itself may be poor.**
   - The window is 10 phases pooled across concurrent games. A player in five games can turn over their whole window in a day.
   - `high` tolerates exactly one NMR in 10. `medium` is a three-value band (2–4), and a single CD moves `high` to `medium`.
   - `low` triggers after 2 phases while the other tiers need 10, an asymmetry that is intended (§2 strong opinion).
   - One order counts as full submission (§4).
4. **Forgiveness was never built** (§2 table).
5. **No context-sensitivity.** Every NMR weighs the same: phase 1 or phase 40, a live game or one everyone else has left, a strong position or one unit left. Production data (§10) shows the CD population is mostly first-three-phase no-shows, plus a smaller group of late abandoners. More than a quarter of those late CDs happened after half the other seats had already gone.
6. **`low` is an absorbing state** (§7.2). The epic's recovery paths, bot games and forgiveness, do not exist, and private games do not count. 399 players active in the last 30 days are `low` (§10).
7. **Loopholes that erase NMRs** (§6.1):
   - An admin "remove" erases the removed player's history in that game, and an admin can only remove an active player who is in CD or NMR'd the last phase (`service/game/models.py:899-911`). The action that answers an NMR deletes the NMR.
   - Taking over a CD seat erases the CD.
   - Failing to muster has no effect on the score.
   - Deleting the account resets everything (§8.6).
8. **Recompute happens only at public phase resolution** (§6.3). Retroactive rated-set changes land late, and a player outside public games never updates.
9. **Two systems disagree by construction** (§8.5), and the dashboard rated set (#1141) deliberately differs from scoring as well. A third population also exists: the staging-game purge on CD (§5).
10. **The tier is invisible where it was meant to matter.** It is on the wire for every member but not shown in lobbies (§8.4).

---

## 10. Production snapshot (2026-10-24)

"Human" means `UserProfile.kind = 'human'`. Monthly figures bucket by `phase.scheduled_resolution`; there is no `resolved_at` column. October is month-to-date.

**Tier distribution.**

| Tier | All human profiles | Humans with a rated phase in the last 30 days |
| --- | --- | --- |
| undefined ("New") | 5,583 (77%) | 660 (38%) |
| high | 624 (9%) | 555 (32%) |
| low | 783 (11%) | 399 (23%) |
| medium | 221 (3%) | 138 (8%) |

For comparison, #1145 recorded undefined 2,881 · high 194 · low 117 · medium 42 in early August.

**Who is `low`?**

- 783 `low` humans in total.
- 325 (42%) never submitted orders in a public game.
- 201 (26%) have 20 or more received phases in public games: established players who slid to `low`.
- 56 have 4 or fewer public phases with possible orders.

**NMR rate, dashboard rated set (#1141).**

| Month | Human seats | Human NMR % | Share of all NMRs from members who entered CD |
| --- | --- | --- | --- |
| 2026-03 | 582 | 42.8 | 0.0 |
| 2026-04 | 2,459 | 37.9 | 4.1 |
| 2026-05 | 8,106 | 35.4 | 69.2 |
| 2026-06 | 17,746 | 30.6 | 90.9 |
| 2026-07 | 35,019 | 20.9 | 84.9 |
| 2026-08 | 56,223 | 13.5 | 81.8 |
| 2026-09 | 68,796 | 13.5 | 84.0 |
| 2026-10 (MTD) | 73,996 | 11.6 | 82.2 |

Bot seats are negligible: 41 in total over the period. The last column counts NMRs on seats whose member has `civil_disorder_at` set, so it includes the post-CD phases that scoring clamps away. It supports the epic's premise that abandoners dominate the metric.

**When players enter CD** (last 120 days; 3,173 CD members). "Phase number" is approximated as the count of the game's phases created up to the CD time.

**Erratum.** This table is wrong. It buckets by `civil_disorder_at`, which was backfilled from `updated_at` for every departure before 2026-10-11, so most of these timestamps fall near game start rather than when CD happened. The "others gone" column is wrong for the same reason. Measured from the phase where CD triggered, about a quarter of CDs happen in phases 1–3, not 87%. See the corrected table in [`02-calibration.md`](./02-calibration.md) §3.

| Phase number at CD | CD members | …of which ≥ half the other seats were already gone |
| --- | --- | --- |
| 1–3 | 2,769 (87%) | 6 |
| 4–8 | 121 | 14 |
| 9–20 | 187 | 49 |
| 21+ | 96 | 29 |

**Departures and replacements.**

- Last 60 days: 1,698 CD entries, 450 removals, 166 withdrawals.
- Replacements all-time: 156 seats, 102 of them CD seats, so those 102 CDs are excluded from scoring.
- Mustering: **0** games have ever had a `muster_deadline`.

**Gating uptake** (non-sandbox games created in the last 90 days): public `open` 1,461 · public `committed` 309 (17% of public) · private 903.

---

## 11. Open questions for the redesign

These are the decisions the current system makes implicitly. A proposal should settle each explicitly.

1. **Unit of judgement.** Phase, game, or departure event? The current score is per phase, clamped per CD.
2. **Context weighting.** Should an NMR's weight depend on:
   - game stage
   - how many other seats are already vacant, or whether the game is effectively over
   - the player's position (units and centres)
   - the phase type
   - whether the game is a "first game"
3. **Which exits count, and how much.** Withdrawal (free today), CD, admin removal and seat takeover (both erasing today), mustering no-show (free today), and account deletion (reset today).
4. **Recovery.** How a `low` player gets back, and whether private or bot games should count toward recovery.
5. **Forgiveness.** Who may ask, how often, what it resets, and what it records.
6. **Window and calibration.** N, the time basis, cut-points, how concurrent games pool, and whether `medium` is a meaningful band. Only 8% of active players are `medium`.
7. **What players see, and where.** Profile, lobby, player list, notifications. What a player is told about their own score and how to change it.
8. **One population or several.** Scoring vs the profile NMR rate vs the dashboard rated set (#1141). Retire `get_player_stats` / `min_reliability`?
9. **Persistence.** Score history, tombstones across account deletion, and an audit of what changed a score.
10. **Interaction with the rest of the epic.** The concurrent cap (§8 of the epic) needs tiers. Bots and mustering change who NMRs and when.

---

## Appendix A: key files

| Concern | File |
| --- | --- |
| Scoring and gating rule | `service/user_profile/commitment.py` |
| Legacy stats and tier | `service/user_profile/utils.py` (`get_player_stats`, `tier_allows_min_reliability`) |
| Outcome recording, CD, recompute hook, staging purge | `service/phase/models.py` (`PhaseManager`) |
| Departures, takeover, withdraw, remove | `service/member/models.py` (`MemberManager`, `Member`) |
| Game gating fields, eligibility, removal rule, abandonment, mustering | `service/game/models.py` |
| Permissions | `service/common/permissions.py` (`MeetsCommitmentRequirement`, `MeetsReliabilityRequirement`) |
| Enums | `service/common/constants.py` |
| Profile API | `service/user_profile/serializers.py` |
| Tests | `service/user_profile/tests.py` (`TestScoreCommitment`, `TestRecomputeCommitment`), `service/game/tests/test_commitment_requirement.py`, `service/game/tests/test_min_reliability.py` |
| Profile UI | `packages/web/src/components/PlayerProfileContent.tsx` |
| Lock UI | `packages/web/src/components/GameCard.tsx`, `packages/web/src/screens/Home/GameInfo.tsx`, `packages/web/src/screens/Home/CreateGame.tsx` |

## Appendix B: production queries

All read-only, run through pgweb (`/prod-query`) on 2026-10-24.

```sql
-- A. tier distribution (all humans)
SELECT commitment, count(*) FROM user_profile_userprofile WHERE kind='human' GROUP BY 1;

-- A'. tier distribution, humans with a rated phase in the last 30 days
SELECT up.commitment, count(DISTINCT up.id)
FROM user_profile_userprofile up
JOIN member_member m ON m.user_id = up.user_id
JOIN phase_phasestate ps ON ps.member_id = m.id
JOIN phase_phase p ON p.id = ps.phase_id
JOIN game_game g ON g.id = p.game_id
WHERE up.kind='human' AND g.sandbox = FALSE AND p.status='completed' AND ps.has_possible_orders
  AND p.scheduled_resolution > now() - interval '30 days'
GROUP BY 1;

-- B. monthly NMR rate (dashboard rated set) and share of NMRs from CD members
SELECT date_trunc('month', p.scheduled_resolution)::date AS month,
  count(*) FILTER (WHERE up.kind='human') AS human_seats,
  round(100.0*count(*) FILTER (WHERE up.kind='human' AND ps.orders_outcome='nmr')
        /NULLIF(count(*) FILTER (WHERE up.kind='human'),0),2) AS human_nmr_pct,
  count(*) FILTER (WHERE up.kind<>'human') AS bot_seats,
  round(100.0*count(*) FILTER (WHERE ps.orders_outcome='nmr' AND m.civil_disorder_at IS NOT NULL)
        /NULLIF(count(*) FILTER (WHERE ps.orders_outcome='nmr'),0),1) AS pct_nmrs_from_cd_members
FROM phase_phasestate ps
JOIN phase_phase p ON p.id = ps.phase_id
JOIN game_game g ON g.id = p.game_id
JOIN member_member m ON m.id = ps.member_id
LEFT JOIN user_profile_userprofile up ON up.user_id = m.user_id
WHERE p.status='completed' AND ps.has_possible_orders AND ps.orders_outcome IS NOT NULL AND g.sandbox=FALSE
  AND p.scheduled_resolution > now() - interval '7 months' AND p.scheduled_resolution < now()
GROUP BY 1 ORDER BY 1;

-- C. gating uptake
SELECT g.private, g.commitment_requirement, count(*) FROM game_game g
WHERE g.sandbox=FALSE AND g.created_at > now() - interval '90 days' GROUP BY 1,2;

-- D. phase number at CD, and whether the game was already half-empty
WITH cd AS (
  SELECT m.id,
    (SELECT count(*) FROM phase_phase p WHERE p.game_id=m.game_id AND p.created_at <= m.civil_disorder_at) AS phase_no,
    (SELECT count(*) FROM member_member o WHERE o.game_id=m.game_id AND o.id<>m.id AND o.kind='player'
       AND o.replaced_by_id IS NULL) AS others,
    (SELECT count(*) FROM member_member o WHERE o.game_id=m.game_id AND o.id<>m.id AND o.kind='player'
       AND o.replaced_by_id IS NULL
       AND (o.civil_disorder_at < m.civil_disorder_at OR o.withdrawn_at < m.civil_disorder_at
            OR o.eliminated_at < m.civil_disorder_at OR o.removed_at < m.civil_disorder_at)) AS others_gone
  FROM member_member m JOIN game_game g ON g.id=m.game_id
  WHERE m.civil_disorder_at IS NOT NULL AND g.sandbox=FALSE AND m.civil_disorder_at > now() - interval '120 days'
)
SELECT CASE WHEN phase_no <= 3 THEN '1-3' WHEN phase_no <= 8 THEN '4-8'
            WHEN phase_no <= 20 THEN '9-20' ELSE '21+' END AS bucket,
  count(*), count(*) FILTER (WHERE others > 0 AND others_gone::float/others >= 0.5)
FROM cd GROUP BY 1 ORDER BY 1;

-- E. departures, replacements, mustering
SELECT 'withdrawn_60d', count(*) FROM member_member WHERE withdrawn_at > now() - interval '60 days'
UNION ALL SELECT 'removed_60d', count(*) FROM member_member WHERE removed_at > now() - interval '60 days'
UNION ALL SELECT 'cd_60d', count(*) FROM member_member WHERE civil_disorder_at > now() - interval '60 days'
UNION ALL SELECT 'replaced_total', count(*) FROM member_member WHERE replaced_by_id IS NOT NULL
UNION ALL SELECT 'cd_then_replaced', count(*) FROM member_member WHERE replaced_by_id IS NOT NULL AND civil_disorder_at IS NOT NULL
UNION ALL SELECT 'games_ever_mustered', count(*) FROM game_game WHERE muster_deadline IS NOT NULL;

-- F. profile of low users (public, non-sandbox phases with possible orders)
WITH lows AS (
  SELECT up.user_id,
    count(ps.id) FILTER (WHERE ps.orders_outcome IS NOT NULL) AS rated_any,
    count(ps.id) FILTER (WHERE ps.orders_outcome='received') AS received
  FROM user_profile_userprofile up
  LEFT JOIN member_member m ON m.user_id=up.user_id
  LEFT JOIN game_game g ON g.id=m.game_id AND g.sandbox=FALSE AND g.private=FALSE
  LEFT JOIN phase_phasestate ps ON ps.member_id=m.id AND ps.has_possible_orders AND g.id IS NOT NULL
  WHERE up.commitment='low' AND up.kind='human'
  GROUP BY up.user_id
)
SELECT count(*), count(*) FILTER (WHERE received=0), count(*) FILTER (WHERE rated_any<=4),
       count(*) FILTER (WHERE received>=20)
FROM lows;
```
