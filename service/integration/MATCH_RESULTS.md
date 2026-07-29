# dumbbot match results

Latest recorded run of `integration/test_dumbbot_match.py`. Update this file
when a new match is played.

- **Date:** 2026-07-29
- **Model:** `claude-haiku-4-5` (`BOT_LLM_MODEL` unset, so the settings default applied)
- **Variant:** classical, `nation_assignment: ordered`, both games driven to Spring 1910 Movement
- **Command:** `pytest integration/test_dumbbot_match.py::<test> -s -q`

Seats follow join order: the test adds every LLM profile before every dumbbot
profile, and `ordered` assignment zips members sorted by id onto the variant's
nation order. The minority bot therefore lands on a fixed power in each game —
Turkey in Game A, Austria in Game B.

## Game A — 6 LLM + 1 dumbbot

Reached Spring 1910 Movement. 17m 48s wall clock, 136 model calls.

| Nation | Kind | Centres | Score |
|---|---|---|---|
| Austria | llm | 2 | 4 |
| England | llm | 3 | 9 |
| France | llm | 5 | 25 |
| Germany | llm | 10 | 100 |
| Italy | llm | 4 | 16 |
| Russia | llm | 1 | 1 |
| Turkey | dumbbot | 9 | 81 |

Cohorts: llm 155, dumbbot 81. Total 236.

## Game B — 1 LLM + 6 dumbbots

Reached Spring 1910 Movement. 4m 38s wall clock, 19 model calls.

| Nation | Kind | Centres | Score |
|---|---|---|---|
| Austria | llm | 2 | 4 |
| England | dumbbot | 4 | 16 |
| France | dumbbot | 5 | 25 |
| Germany | dumbbot | 4 | 16 |
| Italy | dumbbot | 5 | 25 |
| Russia | dumbbot | 6 | 36 |
| Turkey | dumbbot | 6 | 36 |

Cohorts: dumbbot 154, llm 4. Total 158.

## Reading these numbers

Neither game ended early; no power reached the 18 centres needed for a solo, so
both totals are ordinary Spring 1910 positions.

Cohort sums are not a head-to-head result. They aggregate unequal seat counts (6
versus 1), so the larger cohort dominates its game's total by construction, and
sum-of-squares further rewards concentration — Game A's llm cohort owes 100 of
its 155 to Germany alone. Seat assignment is a second confound: `ordered` pins
the minority bot to one specific power, and Turkey (Game A's dumbbot) and
Austria (Game B's llm) are not comparable starting positions.

One game per configuration is a sample of one. Treat these as a recorded
measurement of two specific games, not evidence that either cohort plays better.
