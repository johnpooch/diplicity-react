# Player reliability on other Diplomacy platforms: prior art

**Researched 2026-10-24.** This is the companion to [`00-current-state.md`](00-current-state.md). It describes how other online Diplomacy platforms measure and enforce player reliability, so the redesign questions in §11 of that document can be answered with precedent. It does not propose changes.

## Sources and confidence

| Platform | Source | Version read |
| --- | --- | --- |
| webDiplomacy | [github.com/kestasjk/webDiplomacy](https://github.com/kestasjk/webDiplomacy) | `80d5d26`, 2026-10-23 |
| vDiplomacy | [github.com/Sleepcap/vDiplomacy](https://github.com/Sleepcap/vDiplomacy) | `72c81f0`, 2025-04-21 |
| Original Diplicity (server) | [github.com/zond/diplicity](https://github.com/zond/diplicity) | `4a75c22`, 2024-06-17 |
| Original Diplicity (Android client) | [github.com/zond/android-diplicity](https://github.com/zond/android-diplicity) | `e837682`, 2021-08-03 |
| Backstabbr, playDiplomacy | Public web pages, via search-engine excerpts only | — |

- **Citations.** Code citations are `repo:path:line`, where `repo` is `webDip`, `vDip`, `zond` or `android`, against the commit above. Every code claim was read from the source.
- **Read, not run.** Behaviour derived by following the code rather than by running it is marked **(from reading)**.
- **vDiplomacy repository (unverified).** `Sleepcap/vDiplomacy` is the public vDiplomacy codebase I could find: its files carry vDiplomacy copyright headers and `vDip:` comments. Whether vdiplomacy.com runs this exact commit is unknown.
- **Closed platforms.** The sandbox's network policy blocked direct fetches of backstabbr.com, playdiplomacy.com, webdiplomacy.net and vdiplomacy.com. Everything about Backstabbr and playDiplomacy, and every forum complaint, comes from search-result excerpts of those pages. Those claims are marked **(web)**, cite the URL that was summarised, and should be treated as second-hand. Anything I could not pin down is marked **(uncertain)**.

---

## 1. Summary

| | webDiplomacy | vDiplomacy | Original Diplicity | playDiplomacy (web) | Backstabbr (web) |
| --- | --- | --- | --- | --- | --- |
| **Unit** | Missed phase ("missed turn") | Missed phase, plus CD takeovers | Phase classified as NMR / active / ready | NMR share and surrenders | Turns missed (profile stat) |
| **Score** | Reliability Rating (RR), 0–100% | RR, plus an integer "integrity" | Reliability and Quickness, unbounded ratios | Diplomat / Ambassador class | None found |
| **Window** | 365 days. Extra penalties for misses ≤28 days old (≤7 days in live games) | 365 days | Lifetime | Last 3 games; 97% orders **(uncertain)** | — |
| **Excuses** | Per-game excused delays (0–4, default 3). Each one extends the deadline | Same, default 1. Excuses can be earned back | None | — | — |
| **Exit event** | CD when excuses run out | Same | Probation; seat redacted only if the GM removes the player | Auto-surrender after 2 consecutive movement NMRs | Units hold; GM replaces |
| **Gate** | Creator-set minimum RR per game, and timed bans | Minimum RR, minimum phases, concurrent-game limits, bans | Creator-set minimum Reliability / Quickness | "Ambassadors only" games | None found |
| **Recovery** | Penalties expire after 28 days and 1 year. Moderators can excuse a single miss | Each CD takeover cancels one unexcused miss; excuse regain | Keep playing; the ratio climbs | Complete games **(uncertain)** | — |
| **Global lockout** | Only during a timed ban | Only during a timed ban; the game limit shrinks to 1 | Never | Never **(uncertain)** | Never **(uncertain)** |

The pattern across all of them: **no platform locks a player out of every public game indefinitely.** Each keeps an unrestricted pool, either games with no requirement or the non-Ambassador tier, and uses time-limited bans or caps for the worst cases.

---

## 2. webDiplomacy

### 2.1 What is recorded

Two tables feed the rating:

- **`wD_TurnDate`.** One row per member, per processed phase, for each `Playing` *or* `Left` (CD) member whose country has orders to give (`webDip:gamemaster/members.php:588-609`). `wD_Users.yearlyPhaseCount` is incremented in step and decremented as rows age past 365 days (`webDip:gamemaster/gamemaster.php:220-250`, decrement at `:245`).
- **`wD_MissedTurns`.** One row per `Playing` member who had orders and whose `orderStatus` contains none of `Saved`, `Ready` or `Completed` (`webDip:gamemaster/game.php:592-649`). Saving a single order is therefore enough to avoid a miss, as in our app (`00-current-state.md` §4).

Each missed turn carries three exemption flags:

| Flag | Set when | Effect |
| --- | --- | --- |
| `systemExcused` | The member still had an excused delay left in this game (`game.php:620`) | Counts in the base rate only |
| `samePeriodExcused` | Another unexcused, non-same-period miss exists for this **user, in any game**, in the last 24 h. Non-live games only (`game.php:621-631`) | Counts in the base rate only |
| `modExcused` | A moderator excuses it, with a reason (`webDip:admin/adminActionsSeniorMod.php:112-132`), or excuses a whole outage window (`:134`) | Ignored entirely |

Games against bots (`playerTypes = 'MemberVsBots'`) are skipped for both tables (`game.php:597`, `members.php:594`). "Fill with Bots" games, which top up a short-handed lobby with bots at start (`webDip:gamemaster/adjudicator/pregame.php:234`), still count.

"Live" means phases of 60 minutes or less (`game.php:613`).

### 2.2 Formula

`updateReliabilityRatings` runs every gamemaster cycle (`webDip:gamemaster/gamemaster.php:118`). It buckets missed turns by age (≤7 d, 7–28 d, 28–365 d, expired; `:147-155`) and computes (`:431-440`):

```
RR = 100 × max(0,
       1 − M / Y                          -- base rate
       − 0.11 × U(non-live, ≤ 28 d)
       − 0.05 × U(non-live, 28–365 d)
       − 0.11 × U(live, ≤ 7 d)
       − 0.05 × U(live, 7–28 d))
```

- `Y` is `yearlyPhaseCount`, i.e. phases with orders in the last 365 days.
- `M` is missed turns in the last 365 days that are not moderator-excused. It **includes** system- and same-period-excused misses, live or not (`totalNew`, `:161`).
- `U(...)` counts *unexcused* misses (no flag set) in that age band.

The comment block at `:386-428` documents the same rule with the original subquery form.

**Worked example (from reading).** A player has 200 phases this year. In one game, with the default 3 excuses, they miss 4 deadlines and go into CD:

- 3 system-excused misses and 1 unexcused miss.
- Immediately afterwards: RR = 100 × (1 − 4/200 − 0.11) = **87%**.
- After 28 days: 1 − 0.02 − 0.05 = **93%**.
- After a year: **100%**.

The penalty steps down twice and then vanishes. The base rate is the only part that scales with activity.

**Decay is purely time-based.** The rating is recomputed whenever buckets roll over, whether or not the player is playing (`:220-370`).

### 2.3 Excuses, extensions and civil disorder

- **Excused delays.** The creator picks 0–4 excused delays per player, default 3 (`webDip:locales/English/gamecreate.php:337-339`; validation `webDip:gamecreate.php:213-214`).
- **Extensions.** While any `Playing` member NMRs, the phase is **not processed**. One excuse is removed and the deadline is pushed back by min(phase length, 24 h) (`webDip:gamemaster/game.php:800-813`, `:666-679`; `webDip:gamemaster/members.php:665-677`). Each removed excuse messages the player: "You have missed a deadline and lost an excuse (%s left). Be more reliable!" (`webDip:gamemaster/member.php:505-513`).
- **CD.** With no excuses left, the member is set `Left`, a `wD_CivilDisorders` row is written, and the seat opens for takeover (`members.php:674-677`; `webDip:gamemaster/member.php:333-357`). `activeNMRs` is set before the excuse check (`members.php:670`), so the CD-triggering NMR also extends the phase once. The creator help text says: "The game will only progress with missing orders if no replacement is found within one phase" (`locales/English/gamecreate.php:332`).
- **Excuses don't refresh.** Excuses are a per-game budget. They do not need to be consecutive, and they never come back.
- **One unexcused miss per CD.** After CD, `recordNMRs` only looks at `Playing` members (`game.php:599-605`), so a CD seat accrues no further missed turns. A CD costs the player (excuses used) system-excused misses plus one unexcused miss. This is the same idea as our CD clamp (`00-current-state.md` §6.1), reached a different way.
- **Total abandonment.** If every remaining player NMRs in the same phase, all `Left` players are restored and the game is drawn (`game.php:786-798`).

### 2.4 Leaving, being replaced, rejoining

| Event | Treatment |
| --- | --- |
| Leave before start | Free. Membership deleted, bet refunded (`webDip:gamemaster/member.php:36-60`) |
| Leave after start | No resign action found. A player can only stop ordering (→ CD) or vote draw / concede (`members.php:267`). **(Not exhaustively checked.)** |
| Seat taken over | `wD_Members.userID` is rewritten to the new player (`members.php:532-546`). The old player's missed turns and CD row stay attached to their user ID, so **nothing is erased**. The old player loses their points bet (`member.php:401-412`). The new player **inherits the seat's remaining excuses**: the UPDATE does not reset `excusedMissedTurns` |
| Rejoin own CD seat (before a takeover) | Allowed only if not temp-banned and RR still meets the game minimum (`webDip:objects/member.php:293-301`). The CD row is deleted but `deletedCDs` is incremented, and the profile still adds it to the CD count (`objects/member.php:307-325`, `webDip:objects/user.php:578-579`). Missed turns stay |
| Late-game abandonment | No weighting by stage or position. The only special case is the "everyone NMRed, draw" rule above |

**Quirk (from reading).** `registerTurn` runs at the top of every `process()` call (`game.php:773`). Two things follow:

1. A phase that was extended is counted in `Y` again when it is reprocessed.
2. A `Left` seat nobody takes over keeps adding to its former player's `Y` every phase (`members.php:600`).

Both inflate the denominator of the base rate. Neither is tested here.

### 2.5 Sanctions

A temp ban blocks joining, creating, and rejoining your own CD seat. It does not stop play in current games (`webDip:objects/members.php:144-148`, `webDip:gamemaster/members.php:488`, `webDip:gamecreate.php:241`). The ban is triggered on the unexcused, non-same-period NMR that sends a member into CD (`members.php:691-790`):

| Unexcused non-live misses in the last 365 d | Code passes `days =` | Actually stored | Message tells the player | Profile help text says |
| --- | --- | --- | --- | --- |
| 1–3 | — (warning, with "N more misses will impose a temporary ban") | — | — | warnings |
| 4 | 1 | **5 days** | "1 day" | 1 day |
| 5 | 2 | 10 days | "2 days" | 3 days |
| 6 | 3 | 15 days | "3 days" | 7 days |
| 7 | 4 | 20 days | "4 days" | 14 days |
| 8 | 5 | 25 days | "5 days" | 30 days |
| ≥ 9 | 6 | 30 days | "six days" | infinite |

Sources:

- "Code passes": `members.php:761-786`.
- "Actually stored": `User::tempBanUser` multiplies by `5*24*60*60` (`webDip:objects/user.php:981`, `:984`).
- "Profile help text": `webDip:userprofile.php:576-583`.

Commit `b7035b63` (2023-11-06, "lowered reliability ban time") changed both the ladder and the multiplier, and left the help text and messages stale. The ×5 also applies to moderator bans (`webDip:admin/adminActions.php:667`).

**Live games** (`members.php:719-740`): 0–2 unexcused live misses in 28 days earn a warning; 3 or more earn a "1 day" ban, stored as 5 days. Live misses are never same-period-excused, "to prevent someone from re-taking over their position endlessly" (`game.php:636`).

### 2.6 Gating

- **Per-game minimum.** Each game has `minimumReliabilityRating`, 0–100, enforced on join (`webDip:gamemaster/members.php:484-486`) and on rejoin (`objects/member.php:298-301`).
- **Creator limit.** A creator cannot require more than their own RR minus 1. The form defaults to min(60, own RR − 1) (`webDip:gamecreate.php:208-210`, `:260-268`).
- **Listings.** The "joinable" game lists filter on the viewer's RR and temp-ban status (`webDip:gamelistings.php:112`, `:219`, `:536-552`).
- **No global cutoff.** There is no global RR cutoff and no concurrent-game cap. A low-RR player can still join any game whose minimum is 0.
- **Dormant column.** `wD_Games.minimumNMRScore` exists (`webDip:install/1.71-1.72/update.sql:292`) but nothing reads it.

### 2.7 What players see

- **Profile, visible to everyone.** "Reliability rating: X%" (`webDip:profile.php:718`).
- **Profile, visible to the player and moderators** (`profile.php:706-716`, `userprofile.php:599-730`):
  - un-excused delays / phases this year, and the recent penalty
  - a full breakdown table: week / month / year counts, base reduction, non-live and live penalties, and the arithmetic that produces the RR (`userprofile.php:667`)
  - a list of every missed turn this year, with game, country, turn, live, system / mod / same-period-excused flags, and period. Unexcused rows are highlighted red. Moderators get an Excuse / Unexcuse link per row (`:700-716`)
  - a warning if the rating is stale (`isPhasesDirty`, `:603-606`)
- **Game panel.** "Required Reliability: N%", coloured red if the viewer falls short (`webDip:gamepanel/game.php:482-486`). Each member shows "Delays left: x of y" (`webDip:gamepanel/member.php:439-440`). Below the Join button: "(You are not reliable enough to join this game.)" or "(Due to a temporary ban you cannot join games.)" (`gamepanel/game.php:530-540`).
- **Notifications.** A message is sent on every excuse use, on CD (`member.php:352-354`), and on every sanction step with the running count. A site-wide banner shows while temp-banned, with the remaining time and a link to the moderator forum (`webDip:lib/html.php:737-762`).
- **Intro page.** It explains RR exists and links to the profile (`webDip:locales/English/intro.php:258-262`).

### 2.8 Recovery and forgiveness

- **Time.** The ≤28-day 11% penalty drops to 5%, then to 0 after a year. The base rate falls as new phases are played.
- **Moderators.** They can excuse a single missed turn with a reason (`adminActionsSeniorMod.php:112-132`), or every miss in an outage window (`:134`). Either triggers an immediate recompute.
- **Bans** are timed, apart from the help text's claim of "infinite", which the code no longer implements (§2.5).
- **No self-serve forgiveness flow** was found in the code.

### 2.9 Complaints and exploits

- **A returning player stuck at 66% RR (web).** After a long break, despite few recent misses, a player asked for a one-year-only window or an inactivity reset. Another poster argued site leadership rarely feels the rating's downside (["Reliability Ratings" thread](https://webdiplomacy.net/contrib/phpBB3/viewtopic.php?p=27275); date not visible in the excerpt). This predates the current year-windowed formula **(uncertain)**.
- **Calls for a one-year amnesty (web).** A 2019 thread, ["Reliability Rating Scale with Time"](https://webdiplomacy.net/contrib/phpBB3/viewtopic.php?t=1502), asked for forgiveness of misses after a year. A reply said the opposite problem exists: RR is easy to rebuild by playing more, and live games, which usually have no RR requirement, raise it quickly. That fits the code: live phases add to `Y`, and live unexcused penalties expire after 28 days.
- **The excuse cycle (web).** A player uses their excuses and goes CD. The replacement inherits the seat's remaining budget, often 1. Forum users describe games stalled for weeks this way (["Excused Missed Turns is inefficient?"](https://webdiplomacy.net/contrib/phpBB3/viewtopic.php?t=1690)). The code confirms that webDiplomacy does not reset excuses on takeover (§2.4).
- **Ghost Rating survives a replaced CD (web).** A forum user says a CD has no effect on the player's Ghost Rating (skill) if they are replaced (search excerpt, webDiplomacy forum). That is a skill-rating effect, not RR.
- **Stale documentation (from reading).** The ban ladder (§2.5) is wrong in the help text. So is "live missed turns impact your rating for 28 days total" (`userprofile.php:564`): live misses stay in the base rate `M` for a year. And so is "past 72 hours" in the same-period message (`members.php:713-716`), when the rule is 24 hours.

---

## 3. vDiplomacy

vDiplomacy forks webDiplomacy and keeps its `wD_MissedTurns` / `wD_TurnDate` machinery, excuses and extensions. The differences below are what matter.

### 3.1 Two RR formulas in the code

- **The webDiplomacy formula** in its older subquery form. It recomputes for a game's members every time that game processes (`vDip:gamemaster/members.php:971-990`, called from `vDip:gamemaster/game.php:873`):
  `RR = 100(1 − M/Y) − 6·U(non-live ≤28d) − 5·U(non-live ≤365d) − 6·U(live ≤7d) − 5·U(live ≤28d)`
  Because each band nests inside the next, a recent miss again costs 11.
- **A vDiplomacy-specific cubic formula,** commented "VDips way to handle the Reliability rating" (`vDip:gamemaster/gamemaster.php:118-143`):
  `RR = ((100(1 − (CDs + deletedCDs)/(games + 1)) + 100(1 − NMRs/(phases + 1))) / 2)³ / 10000`
  - Lifetime counts.
  - `NMRs` comes from `wD_NMRs`, which, unlike `wD_MissedTurns`, also records `Left` seats every phase (`vDip:gamemaster/game.php:516-522`).
  - It only runs when an admin triggers a full recalculation (`vDip:admin/adminActionsRestricted.php:899`).
  - It is overwritten by the first formula the next time one of the player's games processes **(from reading)**.
  - A forum excerpt quotes the vDiplomacy profile tooltip as "RR = ((noNMR + noCD)/2)^3" (web, [webDiplomacy forum](https://webdiplomacy.net/contrib/phpBB3/viewtopic.php?t=846&start=20)). So the site has shown the cubic version at some point. Which one players see today is **(uncertain)**.

This is the same failure as problem 9 in `00-current-state.md`: two systems that disagree by construction.

### 3.2 Integrity rating and game limits

- **Integrity** = (CD seats this user took over in the last year) − (unexcused non-live missed turns in the last year) (`vDip:objects/user.php:1584-1606`).
- **Dormant field.** `integrityBalance` is documented as "changeable by a mod to improve a player's integrity rating" (`objects/user.php:274-278`). It is loaded (`:728`) but never used.
- **Sanctions** (`vDip:lib/reliability.php:29-37`). They apply while integrity is at or below the key. The ban is applied on the CD-triggering NMR (`vDip:gamemaster/members.php:907-937`); the game limit applies continuously while integrity stays low.

| Integrity | Temp ban | Concurrent public games allowed |
| --- | --- | --- |
| −4 | 1 day | 5 |
| −5 | 3 days | 4 |
| −6 | 3 days | 3 |
| −7 | 7 days | 2 |
| ≤ −8 | 7 days | 1 |

- **Real days.** Bans are stored in real days. There is no ×5 here (`vDip:objects/user.php:1041`).
- **New-player cap.** This is independent of reliability: fewer than 20 phases played allows 2 concurrent games, fewer than 50 allows 4, fewer than 100 allows 7 (`lib/reliability.php:62-64`). The lower of the two limits applies (`:68`).
- **What counts.** Unfinished, non-defeated, public, more-than-2-player games (`:83-91`). Private games and 2-player variants are exempt (`:159-163`).
- **Pre-game only.** The limit applies only to joining a game in Pre-game (`vDip:gamemaster/members.php:588`). **Taking over a CD seat is never limited.**
- **Country switches.** A player with active "country switches" cannot join or create at all (`lib/reliability.php:118-121`).
- **Minimum phases.** Creators can also require 0/50/100/300/600 phases played (`vDip:locales/English/gamecreate.php:465-471`; enforced at `vDip:gamemaster/members.php:578`).

This is the closest prior art to the epic's §8 concurrent-game cap.

### 3.3 Recovery

- **Takeover compensation.** "Each take-over will compensate one unexcused miss and will so reduce the game limits you experience" (`vDip:locales/English/reliability.php`; mechanism `objects/user.php:1584-1606`, recorded at `vDip:gamemaster/members.php:650-656`). The way back from sanctions is to absorb other people's abandoned seats, which takeovers allow even while game-limited.
- **Excuse regain.** Per game, after *n* consecutive turns without a miss (1, 2, 5 (default), 10, or never), one excuse comes back, up to the starting budget (`vDip:gamemaster/member.php:527-562`; options `vDip:locales/English/gamecreate.php:518-524`). Each regain messages the player.
- **Fresh budget on takeover.** A replacement gets the game's full excuse budget (`vDip:gamemaster/members.php:667`). webDiplomacy does not do this.
- **Default excuses** drop to 1 (`vDip:locales/English/gamecreate.php:491`), against webDiplomacy's 3.

### 3.4 Display

- **RR, visible to everyone** (`vDip:profile.php:749`).
- **Visible to the player and moderators** (`profile.php:229`, `:270-330`): the breakdown, the ban ladder computed from the live sanction table (`:253-266`), "Compensated by Take-Overs Within the Last Year", and the current game limit with its reason.
- **Notice when limited.** Game creation shows "Game-Restrictions in effect. You can join or create N additional games" when limited (`vDip:lib/reliability.php:102-108`, `vDip:gamecreate.php:379`).
- **Takeover announcement.** A takeover posts a game message naming and linking the replaced player: "…replacing <player>. Reconsider your alliances." (`vDip:gamemaster/members.php:690-702`).

### 3.5 Exploits and complaints

- **Integrity farming (inferred, not observed on the site).** A takeover counts as soon as it happens (`takenAtTime`). Taking over a nearly eliminated seat earns +1 integrity at little cost.
- **Excuse churn (web).** A vDiplomacy forum thread, about 7 years old, says the excuse system does not suit long variants. It says that if too many excuses are set, players who quit the site can stall games for weeks, and that appeals go to the moderator forum ([vDiplomacy forum 82717](https://vdiplomacy.com/forum.php?viewthread=82717)).

---

## 4. Original Diplicity (zond/diplicity)

This is the system our app replaced.

### 4.1 Measurement

At every phase resolution, each member is classified into one bucket of a `PhaseResult` (`zond:game/phase.go:986-1003`):

| Bucket | Condition |
| --- | --- |
| **NMR** | On probation: had no orders and was not ready, or was on probation last phase and did nothing since. Elimination clears it (`:986`) |
| **Ready** | Declared ready to resolve |
| **Active** | Had orders but did not declare ready |

- **Clearing probation.** Creating an order or touching the phase state clears probation (`zond:game/order.go:315-318`, `zond:game/phase_state.go:183`).
- **No-option phases count as Ready.** A member with no options is auto-ready (`phase.go:990`), so phases where they could not order count as **Ready (from reading)**. This inflates both scores for players who are often in phases without orders (retreats, builds).
- **Abandoners keep scoring NMRs.** A probation member is auto-ready and auto-DIAS (`:990-991`) and keeps scoring an NMR every phase until they act or are eliminated. There is no CD clamp.
- **Fully abandoned games end.** The game ends when every nation is a "quitter", i.e. NMR, DIAS or eliminated (`:1051`).

### 4.2 Formula

```
Reliability = (Ready + Active) / (NMR + 1)
Quickness   =  Ready / (Active + NMR + 1)
```

(`zond:game/user_stats.go:335-336`)

- **No time basis.** Lifetime counts, no window, no decay, and no upper bound.
- **Public and private kept apart.** Public and private games are computed separately (`user_stats.go:95-100`, filtered by `Private=` at `:326-334`). Gating and leaderboards use the public numbers.
- **The wiki disagrees with the code (web).** The Diplicity wiki defines Reliability as "[phases with orders or checked RDY] / [total phases + 1]", a bounded share ([Creating a game](https://sites.google.com/view/diplicity/home/documentation/creating-a-game)). The code divides by NMR + 1 instead, which is unbounded.

Consequences of the ratio form (arithmetic):

- **A new player scores 0** (0/1).
- **Recovery is slow.** A player with 10 NMRs needs 110 good phases to reach 10.
- **Veterans are effectively immune.** 1,000 phases and 30 NMRs gives about 32, enough to clear any typical requirement even right after abandoning several games.

### 4.3 Exits

- **No voluntary leaving after start.** A game is `Leavable()` only before it starts (`zond:game/game.go:661-663`).
- **GM removal.** Only the game master, or the system, can remove a member from a started game. That redacts the member to "Redacted" and marks the seat `Replaceable` for anyone to join (`zond:game/member.go:208-227`, `:293-301`).
- **History is kept.** Earlier `PhaseResult`s keep the original user's ID, so removal and replacement erase nothing.
- **No CD state.** The probation player simply holds.

### 4.4 Sanctions without a score

- **Staging ejection on NMR.** Every probation player is removed from **all** public staging games they had joined (`zond:game/phase.go:212-229`, `:1284-1290`). This is the same implicit sanction our app inherited (`00-current-state.md` §5).
- **Mustering.** When a mustering game finds unready members, it drops them, returns to staging, and ejects them from all public staging games too (`phase.go:1460-1475`). Mustering writes no `PhaseResult`, so a no-show at muster costs no score.
- **The reminder push warns about both.** "If you don't declare ready and don't provide any orders you will lose Reliability score, and be evicted from all staging game queues." (`phase.go:532`).

### 4.5 Gating

- **Per-game minimums.** Games carry `MinReliability` and `MinQuickness` (`zond:game/game.go:444-445`), plus TrueSkill and "hated" filters. They are checked on join and listing (`game.go:285-290`, `zond:game/member.go:480`).
- **Creator must qualify.** A creator must meet their own requirements (`game.go:960-961`).
- **Client default.** The Android client defaults Minimum reliability to min(own Reliability, 10) (`android:app/src/main/java/se/oort/diplicity/MainActivity.java:830-836`). It labels the field "Minimum reliability (high = active players)" (`android:app/src/main/res/values/strings.xml:216`).
- **Why the default exists (web).** The wiki explains it: games without a minimum "will attract new players who (on average) are very likely to never submit a move".
- **Effect on new players.** Their 0 locks them out of every game with a non-zero minimum. They can play only in games whose creators set 0.

### 4.6 Display and recovery

- **Stats.** Numbers are exposed per user at `/User/{id}/Stats`, with "Top reliable" and "Top quick" leaderboards (`zond:game/user_stats.go:37-73`, `zond:game/handler.go:574-594`). The Android client shows Reliability and Quickness on player stats (`strings.xml:36-37`).
- **Recovery** means playing more phases in unrestricted games. There is no forgiveness, no moderator excuse, and no decay.

---

## 5. playDiplomacy (closed source, web only)

- **Classes (web).** Players are split into "diplomat" and "ambassador" classes "based on their history of surrenders and NMRs". Creators can make "Ambassadors only" games ([help: Game Options](https://www.playdiplomacy.com/help.php?sub_page=Game_Options)).
- **Ambassador threshold (web, third-party, 2024-11-09).** "Ambassadors need to have played the last three games to the end, and have entered orders – when they could – at least 97%". There is also an honorary "Star Ambassador" rank for communicative players that does not gate anything ([Diplomaticon](https://diplomaticon.com/2024/11/09/playdiplomacys-scoring-system-2/)). The window behind the 97% is **(uncertain)**.
- **Auto-surrender (web, 2014).** Two consecutive NMRs in movement ("Orders") steps remove the player as "auto-surrendered", described as a site house rule ([Lecture #2](https://www.playdiplomacy.com/articles/2014/05/22/lecture-2-basic-ordering-rules-mechanics/)).
- **NMR Protect games (web).** "'NMR Protect' games reset if a player NMRs in the first phase of the game. The offending player is auto-surrendered and the game will return to waiting for players" (help: Game Options). This is the only mechanism found anywhere that targets the first-phase no-show directly, which is 87% of our CDs (`00-current-state.md` §10).
- **What counts as an NMR (web, forum).** Finalising counts as not-NMR even with no orders. A missed build or retreat is never an NMR; failing to choose required disbands is ([When is NMR actually given?](https://www.playdiplomacy.com/forum/viewtopic.php?t=59670), [Waive a build without NMR](https://www.playdiplomacy.com/forum/viewtopic.php?f=6&t=37191)).
- **Classicists club (web).** A community club "dedicated to respectful, high-reliability players", whose eligibility relates to finishing games without surrendering (search excerpt). Details are **(uncertain)**.
- **Not found:** the formula's window or decay, how long a player stays a Diplomat, any forgiveness path, and whether surrenders affect the Elo-style rating.

## 6. Backstabbr (closed source, web only)

- **Civil disorder (web).** A country with no orders at adjudication is in civil disorder: units hold, retreats disband, and forced removals take the units farthest from home first ([FAQ](https://www.backstabbr.com/faq)).
- **Replacement (web).** The Gamemaster emails a replacement from the Gamemaster modal and assigns them a country once they confirm. In private games the creator keeps Gamemaster powers, including "replace inactive players" (FAQ).
- **Profile (web).** Public member profiles list games, wins / draws / losses, and "turns made" and "turns missed" with percentages, e.g. "Turns Missed: 7 (0.4%)" ([example profile](https://www.backstabbr.com/member/3ad69deff56c42ebb74dfedcfc868c03)). The window is unknown.
- **No gate found.** No reliability score, join requirement, ban or forgiveness mechanism was found **(uncertain: absence of evidence only)**. Replacement is human-mediated, by the GM, rather than open takeover.

## 7. Others

Searches for other platforms turned up no reliability mechanism with a citable description. Diplomacy.AI and Discord-run leagues were among the platforms looked for. "Backstabbr Extras" ([backstabbr-extras.com](https://backstabbr-extras.com/)) is a third-party extension that adds win and survival statistics to Backstabbr profiles, not reliability.

---

## 8. Comparison against the problems in `00-current-state.md` §9

| # | Our problem | What the others do |
| --- | --- | --- |
| 1 | **Opaque to players** | webDiplomacy and vDiplomacy show players their own arithmetic: every missed turn, its excuse flags and age band, and the formula that produced the rating. They message the player on every excuse used, on CD, and at every sanction step, with "N more misses will…". vDiplomacy also says what the current game limit is and why. Diplicity and Backstabbr show bare numbers |
| 2 | **Weak stats page** | webDiplomacy and vDiplomacy show RR to everyone and the breakdown to the player. Backstabbr shows turns made / missed with a %. Diplicity has leaderboards. None of them counts withdrawals as losses, because none has a no-penalty withdrawal |
| 3 | **Window too short, pooled across concurrent games** | webDiplomacy: a 365-day denominator, so one slip barely moves the base. Recency is a separate additive penalty: 11 points for 28 days, then 5 for a year. Misses within 24 h across *all* games count once for penalty purposes (`samePeriodExcused`), which tackles concurrent-game pooling head on. Diplicity: lifetime. No platform counts partial orders as partial: webDiplomacy, vDiplomacy and playDiplomacy all treat any saved or finalised order as received, as we do |
| 4 | **No forgiveness** | No platform has a self-serve request. The forgiveness tools are: per-game **excused delays** (system-excused misses only touch the base rate); vDiplomacy's **excuse regain** after *n* clean turns; **moderator excuse** of a single miss with a recorded reason; and **moderator excuse by period** for outages |
| 5 | **No context-sensitivity** | No platform weights by game stage, position, or how empty the game is. The partial answers: webDiplomacy and vDiplomacy stop counting once a seat is in CD (one unexcused miss per CD). playDiplomacy's **NMR Protect** resets the game on a first-phase no-show instead of letting it poison the game, which is aimed at the first-phase no-shows that make up most of our CDs. webDiplomacy separates live from non-live |
| 6 | **`low` is absorbing** | Nobody has an indefinite global lockout. webDiplomacy: penalties expire and bans are timed (5–30 days); creators choose a threshold per game, so 0-minimum games stay open. vDiplomacy: concurrent limits rather than a lockout, and **takeovers buy back integrity**, so the way back also fills abandoned seats. Diplicity: games with minimum 0 remain. playDiplomacy: Diplomats can still play non-Ambassador games |
| 7 | **Loopholes that erase NMRs** | In webDiplomacy, vDiplomacy and Diplicity, takeover and removal **keep** the original player's history: misses are keyed to the user, not the seat. Rejoining your own CD seat deletes the CD row but bumps `deletedCDs`, which still shows. Diplicity ejects mustering no-shows from staging but does not score them; playDiplomacy's NMR Protect auto-surrenders them. Account-deletion handling was not checked on any platform |
| 8 | **Recompute only at public phase resolution** | webDiplomacy recomputes every gamemaster cycle from time-bucketed counts, so decay applies even to an idle player. vDiplomacy recomputes per processed game, plus on moderator action. Diplicity recomputes asynchronously on join, leave and resolution |
| 9 | **Two systems disagree** | vDiplomacy is a cautionary example: two RR formulas in one codebase, one only reachable by an admin button. webDiplomacy has one formula but stale help text (ban ladder, live-game decay, "72 hours"). Diplicity kept public and private as explicitly separate populations, with gating on public only |
| 10 | **Invisible where it matters** | webDiplomacy shows the game's required RR, coloured against the viewer, and each member's "Delays left x of y" on the game panel. vDiplomacy names and links the replaced player in-game. RR is on every public profile. playDiplomacy makes reliability a visible class, with "Ambassadors only" games |

Points that recur across the platforms:

- **Separate the base rate from a decaying recency penalty.** webDiplomacy and vDiplomacy keep a long-run miss share and add a time-limited penalty for recent unexcused misses. This answers both the "10 phases turn over in a day" problem and the absorbing state, because the punitive part expires on a clock rather than needing new play.
- **Make excuses a game-level budget that delays the game, not a score write-off.** An excused NMR extends the deadline and still counts lightly. That is the same shape as our NMR extensions (`00-current-state.md` §4), but on by default (3 on webDiplomacy, 1 on vDiplomacy) where ours default to 0.
- **Prefer caps to lockouts.** vDiplomacy's concurrent-game limit, for both new players and sanctioned players, is the only shipped analogue of the epic's §8. It exempts private games, 2-player games and takeovers.
- **Let recovery do useful work.** vDiplomacy's "take over a CD seat to cancel a miss" turns the recovery path into backfill supply, the problem the epic's §4 bot backfill also targets.
- **Key the record to the person, never the seat.** All three open-source platforms do this, which closes our takeover and removal erasure loophole by construction.
