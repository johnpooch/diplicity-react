# Player rating: design

**Date:** 2026-11-03
**Discussion:** [#858](https://github.com/johnpooch/diplicity-react/discussions/858)

This document covers the product decisions and the high-level technical design for a skill rating. The research that informed it, a study of how webDiplomacy rates players, is summarised in §9.

**The constants in §4 were calibrated** in sub-issue 3 (§8) by replaying past games. §4.5 has the results.

---

## 1. Decisions

### Scope

1. **One rating per player.** Ratings are not split by variant or press type.
2. **The algorithm is Glicko-1.** Each game counts as one rating period for each player in it. A player's uncertainty (the rating deviation, RD) grows while they don't play, which replaces any decay penalty.
3. **Everyone starts from scratch.** No past game is rated, partly because of past cheating.
4. **Ratings never gate anything.** There is no minimum rating to join a game and no matchmaking by rating. A queue is deferred.
5. **Only the final result counts.** Civil disorder (CD) and withdrawal do not change a rating directly. Commitment already covers them.

### Which games are ranked

6. **A game is ranked** when it is public, not a sandbox, on a ranked variant, and the creator left the **Ranked** toggle on. The toggle is on by default.
   - Game-master games are always private, so they are never ranked.
   - Anonymous games can be ranked. Anonymity stays a separate toggle.
7. **A variant is ranked** when every playable nation has a handicap row. The owner decides which variants are ranked and sets their handicaps by hand.
8. **Minimum length.** A ranked game only changes ratings if it played at least two full years before it ended (Spring 1903 in Classic). This stops quick agreed draws being farmed.

### Scoring

9. **Pairings.** Each game is broken into head-to-head results, called pairings:
   - The solo winner, or every player in the draw, beats each player who did not win or draw. That is a score of 1.
   - Players in the same draw tie with each other. That is a score of ½.
   - Players who did not win or draw are not paired with each other. No result is recorded between them.
   - Draws always include every surviving player.
10. **Nation handicaps.** Each nation in a ranked variant has a rating offset. Expected results compare `rating + handicap` on each side, so a win with a weak nation is worth more. This matters because players can state nation preferences.
11. **Departed players.** A player whose seat was taken over scores the seat as a loss against the other seats' final occupants.
12. **Replacements can only gain.** If a replacement's result would lower their rating, it is recorded with no change.
13. **Banned players.** Results involving a player later marked for cheating are not recalculated. Conduct marks on profiles tell other players who to avoid.

### UI

14. **Profile.** A **Rating** section goes after Commitment and before Conduct history. It shows:
    - the rating;
    - a **Leaderboard** row showing `#n`, which links to the leaderboard, or "Not ranked yet";
    - **Won**, **Drew** and **Lost** counts for ranked games;
    - "No ranked games yet" when the player has none.
15. **Finished ranked game, player list.** Each row shows only the rating change, such as `+31`, with a `1,530 → 1,561` tooltip. There is no outcome column, because the order of the list already shows who won.
16. **Player detail in a finished ranked game.** This screen shows the before and after rating, the total change, and one row per opponent:
    - the result against them: Beat, Tied or Lost to;
    - their rating;
    - the share of the change that came from that pairing.
    For a replacement whose result was negative, it says their rating can only go up.
17. **Leaderboard screen.** It is ordered by current rating and only lists players whose rating is established (§4.4). Your own row is highlighted and pinned when it is off screen. The screen is linked from Community and from each profile's Rating section, and it has an empty state for launch.
18. **Game creation.** A **Ranked** checkbox sits beside **Committed game**. When the game can't be ranked, the checkbox is disabled and the reason is shown, for example "Private games can't be ranked" or "Not available for this variant yet".
19. **Game info.** A **Ranked** row appears for ranked games. Ranked games get no badge on game cards for now.
20. **"How ratings work" page.** A plain-language page with no formulas, linked from the leaderboard and from the profile's Rating section.
21. **Notifications.** None. Rating changes are shown in the app only.

---

## 2. Data model

There is a new `rating` app, built to [`django-app-architecture.md`](../django-app-architecture.md) from the start.

```
Game.ranked                      bool, fixed when the game is created
User   ─1:1─ Rating              current state
Member ─1:1─ RatingResult        one per rated member per game (append-only)
RatingResult ─1:N─ RatingPairing one per opponent; the rows of the breakdown
Nation ─1:1─ NationHandicap      per-nation offset; set by hand
```

**`Game.ranked`.** It is decided when the game is created and never changes afterwards. Changing a variant or its handicaps later does not affect games that already exist.

**`Rating`.** One row per user. Fields: `rating`, `deviation` and `rated_at`.
- A user with no row is a new player at the default values. Rows are created the first time a player's game is rated.
- The current values duplicate the newest `RatingResult`. The row exists for two reasons:
  - It is the lock target that serialises two games finishing at once for the same player.
  - It gives the leaderboard an indexed column to sort by.

**`RatingResult`.** One row per rated member per game. It is never edited, like `CommitmentEntry`.
- Fields:
  - `rating_before`, `deviation_before`, `rating_after`, `deviation_after`;
  - `handicap`, the value applied to the member's nation, copied at rating time;
  - `protected`, set when a replacement's negative result was recorded as no change.
- Won, Drew and Lost counts come from counting results joined to `Member.won` and `Member.drew`. They are never stored.
- A replacement gets a new `Member` row, and the replaced row keeps `replaced_by` (`member/models.py:315`). So a departed player and their replacement each get their own result.

**`RatingPairing`.** One row per opponent of a rated member.
- Fields:
  - `result`;
  - `opponent`, a foreign key to `Member`;
  - `opponent_rating`, `opponent_deviation`, `opponent_handicap`;
  - `score`, which is 1, ½ or 0;
  - `change`, this pairing's exact share of the total change (§4.3).
- The opponent's name goes through the existing member serialisation, so anonymity is handled the same way as everywhere else.

**`NationHandicap`.** Fields: `nation`, a one-to-one link, and `offset`, in rating points.
- Values are entered by hand through Django admin and seeded by a data migration.
- When a value is changed, results already recorded keep the copy they used.
- A variant is ranked when all of its playable nations (`Nation.non_playable=False`) have a row. There is no separate flag.

---

## 3. When a game is rated

- **Trigger.** Both completion paths end with a `Victory`: a solo win in `phase/models.py:628` and a draw in `game/models.py:1237`. Each of them defers a task, `rate_game`, after the transaction commits.
  - A bug in rating then cannot roll back a phase resolution or a draw.
- **The command.** The task calls `RatingResult.objects.rate_game(game)`, a system-triggered command. Its `only_if` policy checks that:
  - the game is ranked and completed;
  - it reached the minimum length;
  - it has no `RatingResult` rows yet, which makes retries idempotent.
- **Locking.** The command locks the game first, then the `Rating` rows of every rated member in user-ID order. It creates any missing rows before taking the lock.
- **Ratings used.** Every member is rated against the same snapshot of ratings, taken when the game is rated. Not ratings from when the game started.
- **Who is rated.** Human members only, using the same check as `CommitmentEntryManager.record`. Bots are out of scope until bots play in public games.

---

## 4. Calculation

The calculation is a pure module with no ORM access, tested on its own.

### 4.1 Before a game

A player's deviation grows with the time since they were last rated:

`RD = min(√(RD² + c²·t), RD_max)`

- `t` is the time since `rated_at`, in rating periods. A period is 30 days.
- Values:
  - starting rating 1500;
  - `RD_max` 350, also the starting deviation;
  - `c` chosen so that a settled player's deviation returns to `RD_max` after about two years without playing.

### 4.2 Pairings and expectation

The pairings come from §1.9. For a player *i* against opponent *j*:

`E = 1 / (1 + 10^(−g(RDⱼ)·((rᵢ + hᵢ) − (rⱼ + hⱼ)) / 400))`

where *h* is the nation handicap.

The pairings in one game are not independent games, so each pairing is weighted by *w*:
- *w* is 2/(N−1), where N is the number of players in the game.
- This stops a single game shrinking a player's deviation as much as six separate games would.
- Calibration chose the factor of 2 (§4.5).

### 4.3 Update and breakdown

This is the standard Glicko-1 update, with each pairing weighted:

- `1/d² = q² · Σ w·g(RDⱼ)²·Eⱼ(1−Eⱼ)`
- `RD′² = 1 / (1/RD² + 1/d²)`
- `Δ = q·RD′² · Σ w·g(RDⱼ)·(sⱼ − Eⱼ)`

Each pairing's `change` is its own term of that sum, `q·RD′²·w·g(RDⱼ)·(sⱼ − Eⱼ)`. The breakdown therefore adds up exactly to Δ. The UI rounds each row for display.

**Departed players** are paired as losers against the other seats' final occupants. The other players are paired only with whoever occupied each seat when the game ended, so no seat is counted twice.

**Replacements.** When a replacement's Δ is below 0, their `Rating` is left as it was. Their result and pairings are still written, with `protected=True`.

### 4.4 Established ratings

A rating is established when its deviation, after growing for the time since `rated_at`, is at most `RD_ranked`, which is 150 (§4.5).
- The leaderboard filters and ranks on this inside the query, so a player drops off by themselves after a long break, with no scheduled job.
- A player's profile `#n` is a count of established players with a higher rating.

### 4.5 Calibration

2,267 completed public games, from 28 Nov 2025 to 4 Nov 2026, were replayed through `rating/calculation.py`. They involved 2,132 players, and handicaps were set to 0. Games that were too short, included bots or had no finish time were skipped.

- ***w*.** The weight was scored by log loss on each game's results, predicted before the game. A coin flip scores 0.693.
  - 2/(N−1) scored best, at 0.6330. 1/(N−1) scored 0.6367.
  - Any factor from 1.5 to 2 predicts about equally well.
  - Full weight, 6× in Classic, predicts worse than 1/(N−1).
- **Return to `RD_max`.** Moving it from one year to four changes log loss by less than 0.0005. A single year of history can't tell these apart, so two years stays as a product choice. It is worth re-running once ranked games have been live for a while.
- **Period length.** `c` is derived from the return time, so 7, 30 and 90 days give identical results.
- **`RD_ranked`.** The players on the leaderboard after the replay, at 2/(N−1):

  | `RD_ranked` | Leaderboard now | Ever established |
  | --- | --- | --- |
  | 110 | 7 | 9 |
  | 130 | 23 | 34 |
  | 150 | 61 | 75 |
  | 175 | 113 | 137 |
  | 200 | 186 | 242 |

  For scale, 1,953 players were rated in the last 180 days, and 262 of them played 10 or more games.
  - At 1/(N−1) and 110, only one player would be listed.
  - 150 gives a leaderboard of a useful size.
- **Why deviations stay high.** A player who didn't win or draw is paired only with the winners, so one game tells little about them. `c` also adds uncertainty every idle month. An RD of 150 still means about ±300 points at 95%. That is the cost of learning from a few results per game, not something the constants can fix.

---

## 5. API

Every change below adds a new field or a new endpoint. Nothing is renamed or removed.

| Change | Shape |
| --- | --- |
| Create game request | `ranked: bool`. Refused unless the game can be ranked. |
| Game responses | `ranked: bool` |
| Variant responses | `ranked: bool`, derived from the handicap rows |
| User profile response | `rating`, either `null` or `{ rating, rank: int \| null, won, drew, lost }` |
| Member responses in a completed ranked game | `rating_change`, `rating_before`, `rating_after` |
| New: member rating detail | The before and after rating, `protected`, and the pairings: opponent member, opponent rating, score, change |
| Member detail response | `rated: bool`, so the client only requests the rating detail for a rated member |
| New: leaderboard | A paginated list of established players (rank, user, rating), plus the requesting user's own rank |

Completed-game responses are cached through `CompletedPhaseCacheMixin`, so clients must cope with a missing `rating_change` for up to a week.

---

## 6. Launch

- **Seeding handicaps.** A research prompt gathers per-nation results for Classic and the other mature variants from other platforms. The owner reviews the values and seeds them with a data migration.
- **No backfill.** Ratings begin with the first ranked game that completes after launch.
- **When it goes live.** Games can only be ranked once handicaps exist. Seeding the first variant is therefore the launch, so the backend and UI can ship ahead of it without being reachable.

---

## 7. Out of scope

- Matchmaking queue and minimum-rating gates.
- Bots in ranked games.
- Recalculating results after a player is banned.
- Per-variant or per-press-type ratings.
- Push notifications for rating changes.
- A rating-history chart.
- A "Ranked" badge on game cards.

---

## 8. Work breakdown

Sub-issues, in order:

1. **Rating models.** Create the `rating` app with `Rating`, `RatingResult`, `RatingPairing` and `NationHandicap`, admin for `NationHandicap`, and `Game.ranked`.
2. **Glicko-1 calculation module.** Pairings, handicaps, weighting, departed players, protected replacements and the per-pairing breakdown.
3. **Calibration.** Replay historical completed games through the module to choose *w*, `c`, the period length and `RD_ranked`.
4. **Rate games on completion.** The `rate_game` command and deferred task, called from both completion paths.
5. **Ranked games.** `ranked` on game creation, game and variant responses, the creation checkbox with reasons, and the game info row.
6. **Seed nation handicaps.** Research Classic and the mature variants, then a data migration.
7. **Profile rating section.** API and UI.
8. **Rating change in the finished-game player list.** API and UI, including the tooltip.
9. **Rating breakdown on player detail.** API and UI.
10. **Leaderboard.** Endpoint, screen, and links from Community and from profiles.
11. **"How ratings work" page.**

Sub-issue 6 is the launch switch, as §6 explains. The others can merge in any order once their prerequisites are in.

---

## 9. Research: webDiplomacy

webDiplomacy's skill rating is Ghost Rating (GR). It is a zero-sum "pot" model, built into the site in 2020. These are the findings that shaped this design:

- **GR has no measure of uncertainty.** It settles slowly and favours players with many games. Its hall of fame ranks players by **peak** rating and defines "active" by **last login**. *Here:* Glicko's deviation, current rating, and an established-rating filter.
- **The rating follows the seat.** A player who abandons a lost position escapes the result, and whoever takes over that seat absorbs it. This is the community's biggest complaint, and it discourages people from taking over abandoned seats. *Here:* §1.11 and §1.12, modelled on diplomacy.ca.
- **Players never see their change after a game,** so some build their own spreadsheets. *Here:* §1.15 and §1.16.
- **The formulas on webDiplomacy's help page have drifted from its code,** including a reversed sign. *Here:* a plain-language page with no formulas (§1.20).
- **webDiplomacy has no rating gate.** It considered one and rejected it as exclusive, which matches decision 4. It also shows no ratings in in-game player lists.
- **It requires a minimum game length** (Spring 1903) **and excludes games containing bots.** We adopt both.
