# Commitment score: calibration study

**Date:** 2026-10-24
**Answers:** [`01-owner-decisions.md`](./01-owner-decisions.md) §9.1 (point values, bot cap, recovery multiplier) and §9.6 (colour bands).
**Read alongside:** [`00-current-state.md`](./00-current-state.md) for how commitment works today, and `01-owner-decisions.md` §2 for the model being calibrated.

The owner accepted the *shape* of the model in `01` §2.3, not its values. This study proposes values by replaying production history under candidate value sets and checking each against the constraints in `01` §1 and §2.

Every production figure comes from read-only queries run on 2026-10-24 (SQL in [Appendix B](#appendix-b-production-queries)). The raw rows were pulled into local files and the replay ran locally in Python. Figures for events production has never recorded, muster no-shows and bot games, are **modelled** and labelled as such. Anything not checked is marked **(unverified)**.

---

## 1. Summary

**Recommended values**

| Event | Points | Illustrative (`01` §2.3) |
| --- | --- | --- |
| Submitted phase | **+1** | +1 |
| NMR | **−2** | −2 |
| Entering CD | **−10**, once, on top of the NMRs that caused it | −10 |
| Early withdrawal (in the game's first year) | **−1** | −3 |
| Late withdrawal | **0** | 0 |
| Muster no-show | **−1** (modelled) | −1 |
| Recovery boost, while the total is below zero | **×2** on submitted phases | ×2 |
| Seat takeover | **×2** on submitted phases in a taken-over seat, not stacked with the boost | not set |
| Bot-game cap | **+10** | ~+10 |

**Colour bands for totals:** ≤−21 · −20 to −1 · 0 to 10 · 11 to 49 · 50 to 199 · ≥200 (§2.7).
**Square intensity:** red ≤−14 · −13 to −5 · −4 to −1; grey 0; green 1 to 10 · 11 to 24 · ≥25 (§2.8).

**Findings**

- **The illustrative values were close.** The only changes are early withdrawal (−3 → −1, so withdrawing stays cheaper than an NMR, as `01` §2.2 ranks them) and a takeover multiplier of ×2, which keeps every total a whole number.
- **All five constraints pass on real data** (§5). Going silent costs at least 10 points more than withdrawing at every stage. 68 real late CDs in half-empty games come out net positive. A first-year abandoner reaches +2 after nine bot-game phases. Bot-only play stops at +10.
- **The "≤0" population barely depends on the values.** Across the value sets in §9, 53–56% of active humans sit at or below zero. They are new players with only private games (519), abandoners (393), and a handful of others (§6.2). Values decide *how deep* the red goes, not who is in it.
- **Today's `low` players on day one:** all 325 who never submitted stay at or below zero. Of the 201 established players who slid to `low`, 103 come out positive (median 114 submitted phases), and the 98 who don't have a median of 6 CDs in 7 games (§7).
- **Build totals chronologically.** Summing independently computed squares changes 18% of totals and moves 61 players across a band boundary. An append-only ledger updated at each phase resolution is exact and cheap (§8).
- **Correction to `00-current-state.md` §10:** "87% of CDs happen in phases 1–3" is an artefact of a timestamp backfill. Measured from the phase where CD actually triggered, **26%** do. CDs are spread across the whole game (§3). `01` §1.1 cites the 87% figure.

---

## 2. Recommended values in detail

### 2.1 Submitted phase +1, NMR −2

- A submitted phase is the unit, so a player's total reads roughly as "phases played well, minus penalties".
- At +1/−2 a player breaks even at an NMR rate of 33%: **stay positive by submitting at least two phases in every three.** The current `low` cut-off is 50% (`00` §6.2).
- −2 is the smallest whole-number NMR penalty that keeps the `01` §2.2 severity order: NMR (−2) worse than early withdrawal (−1), which is no milder than a muster no-show (−1), which is worse than late withdrawal (0). At −1 an NMR would tie with early withdrawal.
- Of 69 "learners" (no CD, ≥10 rated phases, NMR rate 10–40%), 99% are positive (§9).

### 2.2 Entering CD −10

- With the two NMRs that trigger it (`service/phase/models.py:360-412`), a CD costs **−14**. That matches the owner's −14 anchor for a 1901 abandonment (`01` §2.4). 1,075 of the 1,083 real first-year CD squares score exactly −14.
- A CD square turns positive once the player submitted more than 2 × NMRs + 10 phases before leaving, about six game years of Classical (§4.4). §5.3 has real examples.

### 2.3 Withdrawal: −1 early, 0 late

- **Early** means the withdrawal happened during the game's first year: the phase in progress has the same `year` as the game's first phase. That covers Spring and Fall 1901 in Classical, including retreats and the winter adjustment.
- Why the first year: it is the window in which going silent produces the earliest possible CD. CD needs two consecutive movement NMRs, so the earliest trigger is the first Fall. An early withdrawal is the honest alternative to a first-year CD, so it is the one worth pricing slightly above zero.
- The rule is the same in every variant, and players can understand it without counting phases.
- 30 of the 136 human withdrawals from public games (22%) were early.
- −1 rather than −3, so that leaving properly costs less than one NMR (`01` §1.6, §2.2). With −3, a player who wants out in Spring 1901 does better by submitting junk orders for a year and then withdrawing for free.

### 2.4 Muster no-show −1 (modelled)

- Kept at the illustrative value. 0 games have mustered (`00` §10), so nothing measures this.
- −1 ties with early withdrawal. `01` §2.2 ranks a no-show as milder, but no whole-number value fits between 0 and −1. Both are "close to free"; the tie is deliberate. The model in §10.3 shows why the value matters less than it looks.

### 2.5 Recovery boost ×2

- While the total is **strictly below zero**, each submitted phase counts double. At exactly zero it does not.
- A first-year abandoner (−14) is back at 0 after 7 submitted phases and at +2 after 9. Nine phases is three game years of Classical (§4.4): easy, not trivial (§10.1).
- ×3 makes recovery a five-phase formality and gains nothing on real data (§9). ×1.5 leaves the abandoner at 0 after nine phases, so they fail an "above zero" threshold.

### 2.6 Seat takeover ×2, bot cap +10

- **Takeover:** each submitted phase in a seat the player took over counts +2.
  - The takeover multiplier and the recovery boost **do not stack**. A negative player in a taken-over seat gets ×2, not ×4. The player-facing rule is one sentence: "phases count double while you are below zero or in a seat you took over".
  - ×2 rather than ×1.5 keeps every total and every tooltip a whole number ("Took over · submitted 7 · +14").
  - Effect on the distribution is small: 122 takeover seats by 78 players, adding 1,075 points in total.
- **Bot cap +10:** a positive bot-game event counts only up to the cap: `credited = max(0, min(points, 10 − total))`.
  - NMRs and CDs in bot games still count in full.
  - The cap equals the top of the neutral band (§2.7), so **bot games alone can never take a player out of the neutral band.**
  - A brand-new player reaches +9 with one nine-phase bot game and +10 with two.
- **Bot game:** a game with at least one bot seat when it started. A bot replacing a vacant seat mid-game should not turn a human game into a capped one. This is a proposal; `01` does not define it.

### 2.7 Colour bands for totals

| Band | Total | Typically means | All humans | Active 30 days |
| --- | --- | --- | --- | --- |
| Dark red | ≤ −21 | More than one abandonment | 439 (6%) | 141 (8%) |
| Red | −20 to −1 | One abandonment, or net NMRs | 809 (11%) | 272 (16%) |
| Neutral | 0 to 10 | New, private-only, bot-only, or just recovered | 5,101 (71%) | 657 (38%) |
| Light green | 11 to 49 | One to three good human games | 370 (5%) | 246 (14%) |
| Green | 50 to 199 | Established | 306 (4%) | 250 (14%) |
| Dark green | ≥ 200 | Long record (top tenth of active players) | 190 (3%) | 175 (10%) |

Why these boundaries:

- **−21:** a single first-year abandonment lands between −14 and −18; two land at −28 or below. −21 separates them with margin.
- **0 to 10:** the neutral band is everyone a host has no human evidence about. Its top is the bot cap.
- **11:** one finished, cleanly played human game scores a median of +19 (interquartile range +12 to +25). So the first band above neutral needs human play.
- **50 and 200** split the active players above the neutral band into roughly equal thirds (246, 250, 175).

### 2.8 Square intensity

| Shade | Square value | Typically means | Human squares (n = 12,614) |
| --- | --- | --- | --- |
| Dark red | ≤ −14 | Abandoned with little or no play | 1,716 (14%) |
| Red | −13 to −5 | Abandoned after some play | 1,526 (12%) |
| Light red | −4 to −1 | Net NMRs, no abandonment | 437 (3%) |
| Grey | 0 | Nothing rated yet, or exactly even | 100 (1%) |
| Light green | 1 to 10 | Short or in-progress game, or a bot game | 2,263 (18%) |
| Green | 11 to 24 | A typical full game | 4,440 (35%) |
| Dark green | ≥ 25 | A long, well-played game | 2,132 (17%) |

- Shade is set by the square's **credited** value, the number the tooltip shows, so boosted and capped points count as credited.
- −14 is exactly a first-year abandonment, so dark red reads as "walked away at the start".
- Light green tops out at 10, matching the bot cap, so a bot-game square is never darker than light green.

---

## 3. Correction: when players enter CD

`00-current-state.md` §10 reports that 87% of CDs happen in phases 1–3, and `01` §1.1 builds on it. That figure comes from a backfilled timestamp, not from when CD happened.

**Cause.**
- Until 2026-10-11, CD and elimination were booleans set with `bulk_update(..., ["civil_disorder"])` and `bulk_update(..., ["eliminated"])` (`git show 52dc739^:service/phase/models.py`, lines 404 and 527).
- Kicks used `save(update_fields=["kicked"])` (`git show 52dc739^:service/member/models.py:87`).
- None of these writes touch `updated_at`.
- Commit `52dc739` added `civil_disorder_at`, `eliminated_at` and `removed_at`, and backfilled them from `updated_at` (`service/member/migrations/0018_rebackfill_member_departure_timestamps.py`).
- So for every departure before that deploy, the timestamp is the member row's last ordinary save, usually around game start.

**Evidence.** I compared `civil_disorder_at` with the resolution of the phase where the CD actually triggered: the member's second consecutive movement NMR, the rule in `_check_civil_disorder` (`service/phase/models.py:360-412`).

| CD triggered | CDs | Timestamp within 1 h of trigger | Median lag |
| --- | --- | --- | --- |
| Before the 2026-10-11 deploy | 2,937 | 0% | 111 h early |
| After | 355 | 99.7% | 0 h |

Query D in `00` Appendix B, run only on the 370 CDs after the deploy, puts 18% in phases 1–3. Run on the 3,137 CDs before it, it puts 3,128 there.

**Corrected table.** This uses public, non-sandbox games over the last 120 days, with the phase number taken as the ordinal of the triggering phase. "Others gone" uses departure times rebuilt from phase data as described in §4.3.

| Phase number at CD | CD seats | Share | …of which ≥ half the other seats were already gone |
| --- | --- | --- | --- |
| 1–3 | 719 | 25% | 3 |
| 4–8 | 828 | 29% | 102 |
| 9–20 | 824 | 29% | 140 |
| 21+ | 473 | 17% | 97 |

**Consequences.**
- Mid-game abandonment is the majority case, not drive-by first-year abandonment. "42% of `low` players never submitted an order" (`00` §10) is unaffected, because it doesn't use timestamps.
- Late CDs in half-empty games are about three times more common than `00` reports (237 after phase 8 in public games, against 78 including private), which matters for the net-positive constraint (§5.3).
- Any analysis that uses `civil_disorder_at`, `eliminated_at` or `removed_at` before 2026-10-11 is wrong in the same way. That includes the "others gone" column in `00` §10.
- This document does not edit `00`. It needs a short erratum there.

---

## 4. Method

### 4.1 Data

- Pulled from production: every game, member, phase and user profile, plus all 503,247 phase states, paged by id in blocks of 100,000. Each query took under 1 s (Appendix B).
- **Scope:** public, non-sandbox games (2,528), with ongoing games included. Private games are unrated (`01` §2.4).
- 1 public game has ever had a bot seat. Human: `UserProfile.kind = 'human'`.
- **Populations:**
  - **all humans:** 7,215 human profiles. Players with no public seat score 0.
  - **humans with a public seat:** 2,343.
  - **active:** humans with a completed, non-sandbox phase with possible orders that resolved in the last 30 days. Private games count here, as in query A′ of `00`. That gives 1,741 players, against 1,752 in `00`, because the queries ran at different times of day.

### 4.2 What a square contains

One square per member row: per player, per game, in public non-sandbox games, for members with a user.

- **Phases:** each phase state with `has_possible_orders`, a non-null `orders_outcome`, and a completed phase scores `received` → submitted, `nmr` → NMR.
  - Its time is the phase's resolution, taken as the next phase's `created_at`. `phase.started_at` is always NULL and `updated_at` is unreliable (`.claude/commands/prod-query.md`).
- **CD:** the square stops at the member's second consecutive movement NMR, and −10 is added there, as in `clamp_post_civil_disorder` (`service/user_profile/commitment.py:30-43`).
- **Withdrawal:** an event at `withdrawn_at`, which is a real timestamp. It is early or late by the phase in progress at that time.
- **Takeover:** a member some other member's `replaced_by` points to.
- **Bot game:** a game with a bot member.

### 4.3 The §5 departure rules, and the data fixes they needed

**CD squares stay after takeover.**
- Replaced members keep their phases up to and including the trigger. Today's scorer drops these games entirely (`commitment.py:56-59`).
- `_set_orders_outcome` stops rating a replaced member (`service/phase/models.py:334-358`), so nothing after the takeover exists to drop.

**Host removal counts only the NMRs that happened.**
- No penalty, and no phases dropped beyond those the live code already leaves unrated (`phase/models.py:340-341`).
- `removed_at` is used as a cut-off only after the 2026-10-11 deploy. Before it, the timestamp is too early (§3): 23 of 47 pre-deploy removals have `received` phases after their `removed_at`.

**CDs before CD detection existed.**
- The first `civil_disorder_at` is 2026-04-10. Before then, abandoners kept recording an NMR every phase.
- For a trigger before that date with **no later submission in the game**, the replay derives the CD: 273 squares, 2,173 trailing NMRs dropped.
- Players who NMR'd twice and came back keep those NMRs as ordinary NMRs.

**Other edge cases.**
- 24 flagged CDs show no NMR pattern (legacy flags). Each gets −10 at its last rated phase.
- Members whose user was deleted are skipped: account deletion is a clean slate (`01` §5).

### 4.4 The total, and the bot-game assumption

- The total is built **chronologically**: every event of a player, across all their games, in resolution order, with the boost and cap applied against the running total at that moment. §8 compares this with summing squares.
- **A "quick bot game" is nine submitted phases (modelled).**
  - Human seats in Classical games that played two or more years without leaving average **2.85 rated phases per game year**, and a median of 9 in their first three years (n = 2,391).
  - So nine phases is three game years. Bots confirm immediately, so this is minutes of play (`01` §2.4).

---

## 5. Constraint checks

All checks use the recommended values.

### 5.1 Going silent costs clearly more than withdrawing, at every stage — **pass**

For every real human CD square (3,611), I scored a counterfactual: withdraw at the start of the final NMR run instead of going silent.

| Phase number at CD | Squares | Points saved by withdrawing: min | median | max |
| --- | --- | --- | --- | --- |
| 1–3 | 1,083 | 13 | 13 | 15 |
| 4–8 | 996 | 10 | 15 | 19 |
| 9–20 | 976 | 10 | 16 | 20 |
| 21+ | 556 | 10 | 16 | 20 |

Withdrawing beats going silent by 2 × (NMRs in the run) + 10 + (1 if late). The 10-point minimums are the 24 legacy CD flags with no NMR run. Every other case beats going silent by at least 13.

### 5.2 Withdrawal stays close to free; late costs no more than early — **pass**

- Early −1, late 0, both below one NMR (−2).
- Human withdrawers had a median of 9 submitted phases before leaving, so a withdrawal square is almost always green.

### 5.3 A long, mostly played game abandoned at the end can be net positive — **pass, with real examples**

- 351 human CD squares triggered after phase 8 with at least half the other seats already gone. **68 are net positive** and 13 are exactly zero.
- Across all 1,532 CDs after phase 8, 261 are net positive.
- CD squares at phase 21+ have a median value of 0, and 249 of 556 are positive.

Largest real examples, anonymised:

| Phase at CD | Others gone | Submitted | NMRs | Square |
| --- | --- | --- | --- | --- |
| 50 | 5 of 7 | 38 | 3 | +22 |
| 59 | 4 of 6 | 41 | 6 | +19 |
| 42 | 3 of 6 | 30 | 1 | +18 |
| 47 | 4 of 6 | 33 | 3 | +18 |

- Production games are young: the oldest public game dates from 2025-10. "Submitted every turn for years" is therefore rare in this data.
- The rule that makes such games positive is mechanical: more than 2 × NMRs + 10 submitted phases.

### 5.4 Abandon in 1901, then one quick bot game → small positive — **pass (modelled)**

| First-year CD | Share of real first-year CDs | Total after a 9-phase bot game | Phases needed to reach > 0 |
| --- | --- | --- | --- |
| 2 NMRs (−14) | 99.3% | **+2** | 8 |
| 3 NMRs (−16) | 0.6% | +1 | 9 |
| 4 NMRs (−18) | — | 0 | 10 |

### 5.5 The bot cap stops farming — **pass (modelled)**

- A bot-only player reaches +10 and stops. That holds for 20 bot games in a row and for 5 run concurrently, interleaved phase by phase.
- It holds **only** with a chronological total. If each bot square were instead capped against the total at the moment it started, 5 concurrent bot games would credit +45 (§8).

### 5.6 Severity order (`01` §2.2) — **pass, with one tie**

- Order: CD (−14) < NMR (−2) < early withdrawal (−1) = muster no-show (−1) < late withdrawal (0).
- The tie is explained in §2.4.
- With the illustrative −3, early withdrawal would rank worse than an NMR.

---

## 6. Distributions

### 6.1 Totals

| Population | n | p5 | p10 | p25 | p50 | p75 | p90 | p95 | p99 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| All humans | 7,215 | −27 | −14 | 0 | 0 | 0 | 20 | 84 | 463 |
| Humans with a public seat | 2,343 | −51 | −32 | −14 | −5 | 35 | 155 | 318 | 982 |
| Active 30 days | 1,741 | −28 | −15 | 0 | 0 | 47 | 201 | 395 | 1,082 |

### 6.2 Who sits at or below zero

This is who an "exclude zero or below" threshold keeps out.

| Population | Below 0 | Exactly 0 | At or below 0 |
| --- | --- | --- | --- |
| All humans | 1,248 | 4,913 | 6,161 (85%) |
| Active 30 days | 413 | 535 | 948 (54%) |

The 948 active players at or below zero are:

- 519 with no public seat, who have only played private games;
- 15 seated in a public game with no resolved phase yet;
- 393 with at least one CD;
- 21 net negative from NMRs alone.

Brand-new players are part of the first two groups. This share moved only between 53% and 56% across the value sets in §9.

### 6.3 Bands

See the tables in §2.7 (totals) and §2.8 (squares).

---

## 7. Day one for today's `low` players

These are totals rebuilt from full history under the recommended values. Groups follow `00` §10 "Who is `low`?", and the counts match it exactly.

| Group | n | Median total | At or below 0 | ≤−21 | −20 to −1 | 0 to 10 | 11 to 49 | 50 to 199 | ≥200 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Never submitted in a public game | 325 | −14 | 325 (100%) | 77 | 248 | 0 | 0 | 0 | 0 |
| 1–19 received phases | 257 | −20 | 255 (99%) | 128 | 127 | 2 | 0 | 0 | 0 |
| 20+ received phases | 201 | +2 | 98 (49%) | 65 | 32 | 17 | 38 | 32 | 17 |
| (≤4 public phases, overlaps the first group) | 56 | −14 | 56 (100%) | | | | | | |
| All `low` | 783 | −14 | 678 (87%) | 270 | 407 | 19 | 38 | 32 | 17 |

- **Established `low` players split cleanly.**
  - The 103 who come out positive have a median of 114 submitted phases and 3 CDs.
  - The 98 at or below zero have a median of 41 submitted phases and **6 CDs in 7 games**: serial abandoners who happened to play a lot.
- **Every `low` player can now recover.**
  - At −14, recovery is about nine bot-game phases.
  - At the dark-red median of the `low` group, it is a few bot games.
  - Today there is no way back at all (`00` §7.2).
- **Other tiers on day one:**
  - `high` (625): median +71, 2 at or below zero.
  - `medium` (221): median +10, 69 at or below zero, 49 of them with exactly one CD.
  - `undefined` (5,586): 97% at or below zero, almost all exactly 0. 506 are negative. They have a CD that today's 10-phase window either never rated as `low` or erases (takeover or removal, `00` §6.1); the split between the two is **(unverified)**.

---

## 8. Chronological total versus summed squares

The recovery boost and the bot cap depend on the running total, so the order of events matters. I compared the exact chronological replay with three cheaper approximations, over the 2,343 humans with a public seat:

| Approximation | Players whose total differs | Mean abs. difference | p99 | Max | Band changes | Crosses zero |
| --- | --- | --- | --- | --- | --- | --- |
| Squares in order of their last event, boost and cap applied within each square against earlier squares | 427 (18%) | 1.5 | 28 | 96 | 61 | 4 |
| Same, squares in order of joining | 448 (19%) | 1.6 | 32 | 108 | 81 | 25 |
| Plain sum of squares, no boost | 420 (18%) | 1.3 | 24 | 129 | 43 | 22 |

The differences come from players with several games running at once while their total is negative.

**Recommendation: an append-only ledger, built chronologically.**

- At each phase resolution, for each player with a rated state:
  1. lock their profile row;
  2. compute the event's credited points from the current stored total;
  3. add the points to both the square and the total, in one transaction.
- Withdrawal and CD are handled the same way at the moment they happen.
- Then:
  - the stored square values are what the grid shows;
  - their sum always equals the stored total;
  - each update is O(1).
- §5 removed every retroactive rule. Takeover no longer erases a CD, and removal no longer erases history. So nothing needs recomputing after the fact.
- A full rebuild, for migration or repair, is the replay this study ran: every event of every player, sorted by resolution time with a deterministic tie-break (resolution time, then member id, then phase ordinal).
- Summing independently computed squares is not close enough. It moves 61 players across a band boundary, and it breaks the bot cap under concurrency (§5.5).

---

## 9. Alternatives considered

Each row changes one thing from the recommended set.

- **First-year CD:** cost of 2 NMRs plus the CD.
- **Active ≤0:** share of active players at or below zero.
- **Deep red:** active players at ≤−21.
- **Est. low +:** share of the 201 established `low` players who come out positive.
- **Late CD +:** share of the 351 late CDs in half-empty games that are net positive.
- **Learners +:** share of the 69 learners (§2.1) who are positive.
- **Serial ≤0:** share of the 541 serial abandoners who stay at or below zero. A serial abandoner has ≥2 CDs, in at least half their public games.
- **1 CD, 30+ submitted +:** share of the 130 players with exactly one CD and 30+ submitted phases who are positive.

| Value set | First-year CD | Break-even NMR rate | Active ≤0 | Deep red | Est. low + | Late CD + | Learners + | Serial ≤0 | 1 CD, 30+ submitted + |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Recommended** | −14 | 33% | 54% | 141 | 51% | 19% | 99% | 89% | 100% |
| Illustrative §2.3 (early −3, takeover ×1.5 stacked) | −14 | 33% | 55% | 141 | 51% | 19% | 99% | 89% | 100% |
| Softer CD, c −6 | −10 | 33% | 53% | 75 | 61% | 32% | 99% | 83% | 100% |
| Harsher CD, c −15 | −19 | 33% | 56% | 174 | 39% | 7% | 99% | 93% | 99% |
| Lenient NMR, n −1 and c −12 | −14 | 50% | 53% | 129 | 54% | 23% | 100% | 88% | 100% |
| Strict NMR, n −3 and c −8 | −14 | 25% | 56% | 146 | 46% | 16% | 87% | 91% | 98% |
| No boost, ×1 | −14 | 33% | 55% | 148 | 49% | 17% | 99% | 90% | 98% |
| Boost ×3 | −14 | 33% | 54% | 137 | 51% | 21% | 99% | 89% | 100% |

Why each alternative lost:

- **Softer CD (−6).**
  - Let 17% of serial abandoners out of red, against 11%.
  - Narrows the gap between going silent and withdrawing to 9 points.
  - It does turn more late CDs positive, but the constraint is "can come out positive", and −10 already does that for 68 real cases.
- **Harsher CD (−15).** Turns only 7% of late half-empty CDs positive and keeps 61% of established `low` players at or below zero, for a 4-point gain on serial abandoners.
- **Lenient NMR (−1, with c −12).**
  - Almost identical on the data.
  - Loses on the severity order: an NMR would tie with early withdrawal.
  - Its 50% break-even repeats today's `low` cut-off, which the epic's under-5% NMR goal is meant to move past (`00` §2).
- **Strict NMR (−3, with c −8).** 13% of learners go negative. That is exactly the "sincere players who are still learning" whom `01` §1.1 says should get in.
- **Boost ×1 or ×3.** Barely changes the historical data. The choice is about the recovery cost of bot games (§2.5, §10.1).
- **Bot cap 5 or 20 (modelled).**
  - Below 10, a one-game newcomer can't establish a visible record.
  - Above 10, bot-only players reach the band that is meant to mean human evidence.
- **Takeover ×1.5, stacked with the boost.** Produces half-points, and ×4 for a negative player in a taken-over seat. Takeover is 122 seats, so the value doesn't move the distribution.
- **Early/late withdrawal boundaries:**
  - **By phase count (for example, the first 5 phases):** differs between variants and is harder to explain.
  - **By the player's own submitted phases:** rewards waiting before leaving.
  - **By the share of other seats gone:** makes the price depend on other players.
  - With early at −1 the boundary moves at most one point, so the simplest rule wins.

---

## 10. Modelled scenarios

### 10.1 Bot recovery (modelled)

Total after a bot game of K submitted phases, starting from a first-year CD:

| Boost | 2 NMRs, K=6 | K=9 | K=12 | 3 NMRs, K=9 | 4 NMRs, K=9 | Phases to reach > 0 (2 / 3 / 4 NMRs) |
| --- | --- | --- | --- | --- | --- | --- |
| ×1.5 | −5 | 0 | +3 | −2 | −4 | 10 / 11 / 13 |
| **×2** | −2 | **+2** | +5 | +1 | 0 | **8 / 9 / 10** |
| ×3 | +2 | +5 | +8 | +5 | +3 | 5 / 6 / 7 |

### 10.2 Serial abandonment (modelled)

A player who repeats "first-year CD, then one 9-phase bot game" has these running totals: −14, +2, −12, +3, −11, +4, −10, +4.

- They pass an "above zero" threshold after every bot game.
- The grid shows the pattern, as `01` §3.2 intends.
- Their total never leaves the neutral band.

### 10.3 Mandatory mustering (modelled)

Assumption: a first-year CD in which the player never submitted (1,081 of the 3,611 human CD squares) would instead have been a muster no-show at −1.

| Share converted | Active ≤0 | Active ≤−21 | Never-submitted `low`, median |
| --- | --- | --- | --- |
| 0% (history as recorded) | 948 | 141 | −14 |
| 50% | 946 | 110 | −14 |
| 100% | 943 | 81 | −1 |

- Mustering hardly changes who is at or below zero: a no-show at −1 is still at or below zero.
- It shrinks the dark-red band by up to 43%, and it makes a drive-by player's recovery two bot phases instead of nine.
- This is the "mild" outcome `01` §2.2 asks for, so −1 needs no adjustment.

---

## 11. Open risks

1. **The 87% premise in `01` §1.1 needs revisiting** (§3). The principle "restrictions target insincerity, not imperfection" still holds. But most CDs are mid-game, so the communication work in `01` §6, making withdrawal the obvious exit, matters more than first-game onboarding.
2. **An "above zero" threshold is one bot game away for every abandoner** (§10.2). A threshold of "above 10", the bot cap, would mean "has a positive record from human games". It also excludes every newcomer who has only played bots. The owner may want to offer it as the suggested setting.
3. **Bot-game definition.** "A bot seat at start" is a proposal (§2.6). Once bot replacement ships (`01` §8), check that a replaced seat does not cap the remaining humans.
4. **Data caveats (unverified in detail).**
   - Phases resolved before the outcome backfill (`service/phase/migrations/0015_backfill_orders_outcome.py`) count a state as `received` if *any* order row exists. That includes the implicit hold orders adjudication creates for some failed units (`service/phase/models.py:618-640`).
   - The 273 derived pre-April CDs rest on the trailing-NMR pattern.
   - Neither affects the recommended values; both affect individual day-one totals.
5. **Young data.** The oldest public game is a year old. Totals for long-tenured players, and how often long games end in a positive CD, will grow. Re-run this study once a year of post-redesign data exists.
6. **Behaviour changes.** Every figure replays past behaviour under new prices. Cheaper withdrawal and visible grids should shift CDs towards withdrawals. That makes the negative tail shallower than shown here, not deeper.

---

## Appendix A: replay script

The replay is a set of Python scripts kept outside the repository. They:

1. load the Appendix B pulls into pandas;
2. build per-member event lists following §4.2 and §4.3;
3. replay each candidate value set chronologically per player, applying the boost while the running total is below zero and the cap per bot-game event;
4. compute the cohorts used throughout: all humans, active, the `00` §10 `low` groups, learners, serial abandoners, and CD stage with "others gone";
5. run the three approximations in §8 and the synthetic players in §10.

A rerun needs only the Appendix B queries and about 20 seconds of local compute.

## Appendix B: production queries

All read-only, run through pgweb (`/prod-query`) on 2026-10-24. Large tables were paged; no query ran longer than 1 s.

```sql
-- B1. table sizes (planning the pull)
SELECT 'games', count(*) FROM game_game
UNION ALL SELECT 'games_public_nonsandbox', count(*) FROM game_game WHERE sandbox=FALSE AND private=FALSE
UNION ALL SELECT 'members', count(*) FROM member_member
UNION ALL SELECT 'phases', count(*) FROM phase_phase
UNION ALL SELECT 'profiles', count(*) FROM user_profile_userprofile
UNION ALL SELECT 'ps_min_id', min(id) FROM phase_phasestate
UNION ALL SELECT 'ps_max_id', max(id) FROM phase_phasestate
UNION ALL SELECT 'ps_public', count(*) FROM phase_phasestate ps
  JOIN phase_phase p ON p.id=ps.phase_id JOIN game_game g ON g.id=p.game_id
  WHERE g.sandbox=FALSE AND g.private=FALSE;

-- B2. games
SELECT id, status, sandbox, private, anonymous, variant_id, created_at, started_at, finished_at,
  muster_required, muster_deadline, nmr_extensions_allowed, commitment_requirement, movement_phase_duration
FROM game_game;

-- B3. members (departure timestamps, takeover links)
SELECT id, game_id, user_id, kind, nation_id, created_at, won, drew, mustered_at, eliminated_at,
  civil_disorder_at, removed_at, withdrawn_at, replaced_by_id
FROM member_member;

-- B4. phases
SELECT id, game_id, ordinal, status, type, season, year, scheduled_resolution, started_at, created_at
FROM phase_phase;

-- B5. profiles (kind, current tier)
SELECT up.user_id, up.kind, up.commitment, u.date_joined, u.last_login
FROM user_profile_userprofile up JOIN auth_user u ON u.id = up.user_id;

-- B6. variants and nation counts
SELECT v.id, v.name, (SELECT count(*) FROM nation_nation n WHERE n.variant_id = v.id) AS nations
FROM variant_variant v;

-- B7. phase states, paged by id in blocks of 100,000 (:lo = 0, 100000, … 1400000)
SELECT ps.id, ps.member_id, ps.phase_id, ps.has_possible_orders, ps.orders_outcome,
  ps.orders_confirmed, ps.eliminated
FROM phase_phasestate ps
WHERE ps.id > :lo AND ps.id <= :lo + 100000;
```

Everything else in this document, including the reproduction of `00` §10's tier and `low`-group counts, was computed locally from B2–B7.
