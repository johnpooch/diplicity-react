# Player commitment redesign: owner decisions

**Date:** 2026-10-24
**Input to:** a proposal for redesigning how Diplicity measures and acts on player commitment.
**Read alongside:** [`00-current-state.md`](./00-current-state.md), which describes how the current system works, production data, and known problems.

These decisions came out of an interview with the owner, John. They are product decisions and the reasoning behind them, not a design. Where numbers appear they are **illustrative**: the owner accepted their shape, not their values. Final values should be calibrated against historical data (see §9).

---

## 1. Principles

1. **Restrictions target insincerity, not imperfection.** Many `low` players are confused or drive-by: 42% of them never submitted an order. Abandonment is different: most CDs happen mid-game, not in the first year ([`02-calibration.md`](./02-calibration.md) §3). Sincere players who are still learning should get in.
2. **Surface facts and let the community decide.** Prefer clear information plus host control over system enforcement. Keep automatic rules few and simple.
3. **Every penalty has a visible, easy way back.** Under the current system `low` is effectively a permanent ban (current-state §7.2). That was never intended.
4. **One robust flow.** No branching onboarding, join paths or game-start paths. Avoid toggles and settings wherever possible.
5. **Clarity is non-negotiable.** Players must understand the rules before their first game and be told plainly what happened and what they can do.
6. **Leaving properly beats going silent.** No one should be forced to keep playing a game they don't want, but going silent must always cost more than an announced exit.

---

## 2. Scoring model

### 2.1 Unit and total
- **The unit of judgement is the game.** Each game a player has been in produces one scored entry, a "square". This replaces the current 10-phase window pooled across games.
- **Ongoing games are scored too.** A game doesn't need to be finished to count, positively or negatively. A game's square updates as its phases resolve.
- **A player's total is the lifetime sum of their squares.** No time decay, no recency weighting, and old squares stay on the record.
  - *Reasoning:* show facts and let hosts interpret them, rather than adding derived nuance.
  - *Accepted cost:* a long-tenured player who recently burned out (for example 200 green squares followed by 5 red) keeps a high total. Hosts are expected to notice the recent red on the grid.

### 2.2 Severity by event
Ordered from worst to mildest:

1. Going silent until civil disorder (CD)
2. Other NMRs
3. Early withdrawal
4. Muster no-show (mild: no one's game was harmed, but the silence is still a signal of flakiness)
5. Late withdrawal (close to free)

Rules that follow from this:
- **Withdrawal must stay clearly cheaper than going silent.** If the gap narrows, players will go silent instead.
- **Withdrawal stays essentially free.** It is the better outcome for everyone compared with abandoning. Withdrawing early may cost a little more than withdrawing late.
- **A long, mostly played game that ends in abandonment can come out net positive.** Example: a player submits every turn for years, then stops in a dead game where most other seats are already gone and they hold two centres. Most of their record is good, and the score should reflect that.

### 2.3 Illustrative values (for calibration, not final)

| Event | Points |
| --- | --- |
| Submitted phase | +1 |
| NMR | −2 |
| Entering CD | −10, applied once, on top of the NMRs that caused it |
| Early withdrawal | −3 |
| Late withdrawal | 0 |
| Muster no-show | −1 |

### 2.4 What counts
- **No weighting by phase length or deadline.** A curve was considered and rejected as too complicated.
- **Private games stay unrated.**
  - Counting them would penalise casual friend groups, who happily wait for each other.
  - It would also enable farming with alternate accounts.
- **Bot games count, but are capped.**
  - Bot games count fully only while the player's total is below a small positive cap (illustratively about +10). Above the cap they contribute nothing.
  - The square still appears on the grid, with a note that the cap was reached.
  - This cap is the main anti-farming mechanism.
- **Recovery boost.** While a player's total is negative, each submitted phase counts extra (illustratively double).
  - Recovery should be easy but not trivial. The target is roughly one quick bot game.
  - Bots confirm as soon as all humans have confirmed, so a bot game takes minutes, not weeks.
  - Example: a player abandons in 1901 and drops to about −14. One bot game brings them back to a small positive total.
- **Seat takeover earns a commitment multiplier.**
  - Taking over a vacant seat is behaviour to encourage.
  - A separate "karma" score was considered and rejected as overkill while takeover is the only good deed tracked.

### 2.5 Named tiers are retired
- `high` / `medium` / `low` / `undefined` and the `committed` game option are replaced by the numeric total.
- A colour scale on totals can indicate when a total is very good or bad. This is a visual band, not a gate.

---

## 3. Display

### 3.1 Commitment grid
- The profile shows a grid styled like GitHub's activity grid, with one square per game.
- Squares are green or red, with colour intensity showing severity. Ongoing games are included.
- Hovering or tapping a square says what happened and its exact effect on the score. Examples:
  - "Submitted 6, missed 1 · +4"
  - "Didn't confirm during mustering · −1"
  - "Bot game · submitted 10/10 · +5 counted (bot cap reached)"

### 3.2 Who uses it
- **The player.** They can see exactly how their total is built, which fixes the current opacity (current-state §9.1).
- **Hosts and other players.** They can judge commitment at a glance.
- **Repeat offenders are caught by hosts reading the grid, not by automatic rules.** For example, a pattern of red, bot-green, red.

### 3.3 Anonymous games
- Commitment (grid and total) is **hidden** in anonymous games. This is the simplest path for now.
- Creator thresholds still apply, so unreliable players are kept out mechanically.
- *Accepted cost:* a recently recovered serial abandoner who is just above zero passes an "above zero" threshold and is invisible to the host.
- **Possible later revisit:** splitting anonymity into "identities hidden" versus "identities known, nations hidden". Showing identities before and after the game but not during it would also help with player reporting. This needs community feedback. Avoid multiplying game settings.

---

## 4. Joining and gating

- **Players join freely, and the host can remove them during mustering.**
  - Request-to-join was considered and rejected because it makes the host a bottleneck for every seat.
- **Mustering is mandatory for public games.**
  - The host must confirm too, so the roster review happens as part of an existing step rather than as a separate chore.
  - Over-the-air app updates now make shipping mustering feasible.
- **Creators may set an optional threshold on the total, and only on the total.**
  - The likely common use is "exclude players at zero or below".
  - No finer-grained controls, such as "no red squares in the last N games".
  - *Accepted cost:* "exclude zero" also excludes every brand-new player.
- **Seat takeover follows the same gate as joining.** A player whose total would have kept them out of a game cannot take over a seat in it.
- **New and unproven players are not blocked.**
  - When an unproven player tries to join, a notice suggests a quick bot game to establish a record. This is a nudge, not a requirement.
  - Experienced newcomers from other platforms can skip it and explain themselves to the host by message.
  - Self-declared experience is acceptable here because a human judges it, and the realistic risk is confusion, not lying.
- **Rejected options:**
  - mandatory bot or tutorial gates before the first public game
  - restricting unproven players to small variants (established players would then avoid those variants)
  - a self-declared "experienced player" flag as a system gate

---

## 5. Departures

| Event | What goes on the grid |
| --- | --- |
| Player enters CD, seat later taken over | The CD square stays. Takeover no longer erases it (today it does, current-state §6.1) |
| Host removes an active player | Only the NMRs that actually happened. **Removal is never treated as abandonment**, so it can't be used as a punishment lever, and removing a player promptly can spare them a CD |
| Host removes a player during mustering | Nothing beyond any muster no-show |
| Withdrawal | See §2.2 |
| Account deletion | **Clean slate.** No tracing of returning players. Since recovery is easy, deleting gains a player little beyond a clean grid |

---

## 6. Communication

- **First game:** explain clearly, at the point of joining, that submitting orders matters and how commitment works.
- **Onboarding email:** the rules in simple terms.
- **Event emails** (email chosen because the game state is complex to explain in-app):
  - when the player's own commitment changes, saying what happened and why
  - when another player in the game enters CD, saying what happened and what the remaining players can do: find a human replacement, bring in a bot, propose a draw, or withdraw
- **In-app clarity on exits.** Make withdrawal obvious as the penalty-free alternative to abandoning. Make sure players know that abandoned players auto-accept draws, so a game with one or two active players can be ended immediately.

---

## 7. Dropped

- **Forgiveness**, the self-service reset from the epic (§12). Bot-game recovery replaces it, and a reset would wipe a player's good history along with the bad.
- **Weighting by phase length.**
- **Language and chattiness as join criteria.** Out of scope.

---

## 8. Dependencies

- **Bot replacement must work for players.** Today it exists only as a management command (current-state §2).
  - Ship an **algorithmic bot** in the interim to unblock bot replacement and bot-game recovery.
  - Replace it with the full LLM bot system later.
- **Bot games must be available to everyone.** They are currently limited to an email allowlist. Recovery depends on this.
- **Mandatory mustering for public games** (§4).

---

## 9. Still open

1. **Point values, bot cap and recovery multiplier.** Calibrate with a data study of historical production data, for example run by a Claude Code instance. The aim is values that produce a sensible distribution of totals and of the colour bands.
2. **Migration.**
   - How to build grids and totals from existing history.
   - How to treat games currently excluded from scoring by the old rules (CDs erased by takeover or removal).
   - What existing `low` players see on day one.
   - This needs care.
3. **Retiring the legacy system** (`get_player_stats`, `reliability_tier`, `Game.min_reliability`, `MeetsReliabilityRequirement`) and existing `commitment_requirement` games. This also needs care.
4. **Concurrent-game cap** (epic §8). Keep it, but redesign it around totals instead of tiers. How is not yet decided.
5. **Anonymous game modes.** See §3.3; needs community feedback.
6. **Colour bands for totals.** Where the boundaries fall.
