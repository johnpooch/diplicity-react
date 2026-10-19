import random
from collections import Counter
from collections.abc import Awaitable, Callable
from functools import lru_cache

from dumbbot.policy import select_orders as dumbbot_select_orders
from engine.positions import Board
from engine.rules import load_variant
from select_orders.constants import PhaseType
from select_orders.context import fixture_to_context
from select_orders.fixtures import full_option, max_orders
from select_orders.options import option_id

VARIANT = "classical"
HORIZON = 1905
HORIZON_REACHED = "horizon"
SOLO = "solo"
ELIMINATED = "eliminated"
SUPPLY_CENTER_MAJORITY = "supply-center-majority"

Policy = Callable[[dict], Awaitable[dict]]


@lru_cache(maxsize=1)
def board() -> Board:
    return Board(load_variant(VARIANT))


def nations() -> list[str]:
    return sorted(board().nation_ids)


def solo_centres() -> int:
    return next(
        condition["supplyCenters"]
        for condition in board().variant["victoryConditions"]
        if condition["type"] == SUPPLY_CENTER_MAJORITY
    )


def opening() -> dict:
    initial = board().variant["initialState"]
    names = board().nation_names
    return board().game_state(
        initial["phase"],
        [
            {"type": unit["type"], "nation": names[unit["nation"]], "province": unit["location"]}
            for unit in initial["units"]
        ],
        [{"nation": names[center["nation"]], "province": center["province"]} for center in initial["supplyCenters"]],
    )


def centres(state: dict) -> dict[str, int]:
    counts = Counter(board().nation_names[center["nation"]] for center in state["supplyCenters"])
    return {nation: counts[nation] for nation in nations()}


def position(phase: dict, units: list[dict], supply_centers: list[dict], nation: str, options: list[dict]) -> dict:
    result = {
        "variant": VARIANT,
        "nation": nation,
        "phase": phase,
        "units": units,
        "supply_centers": supply_centers,
        "order_options": options,
    }
    if phase["type"] == PhaseType.ADJUSTMENT:
        result["max_orders"] = max_orders(nation, units, supply_centers)
    return result


def opening_position(nation: str) -> dict:
    state = opening()
    return position(
        dict(state["phase"]),
        board().fixture_units(state["units"]),
        board().fixture_supply_centers(state["supplyCenters"]),
        nation,
        board().options_by_nation(state)[nation],
    )


def dumbbot(seed: int, nation: str) -> Policy:
    rng = random.Random(f"{seed}:{nation}")

    async def turn(here: dict) -> dict:
        return {"orders": dumbbot_select_orders(fixture_to_context(here), rng=rng)}

    return turn


def dumbbot_seats(seed: int) -> dict[str, Policy]:
    return {nation: dumbbot(seed, nation) for nation in nations()}


def _submitted(options: list[dict], chosen: list[dict]) -> list[dict]:
    legal = {option_id(full_option(option)): option for option in options}
    submitted, ordered = [], set()
    for option in chosen:
        match = legal[option_id(full_option(option))]
        province = match["source"].split("/")[0]
        if province not in ordered:
            ordered.add(province)
            submitted.append(match)
    return submitted


def _end(state: dict, nation: str, horizon: int) -> str | None:
    if state["phase"]["type"] != PhaseType.ADJUSTMENT:
        return None
    held = centres(state)
    if max(held.values()) >= solo_centres():
        return SOLO
    if held[nation] == 0:
        return ELIMINATED
    if state["phase"]["year"] >= horizon:
        return HORIZON_REACHED
    return None


async def play(policies: dict[str, Policy], nation: str, *, state: dict | None = None, horizon: int = HORIZON) -> dict:
    state = state or opening()
    phases = []
    while (end := _end(state, nation, horizon)) is None:
        phase = dict(state["phase"])
        units = board().fixture_units(state["units"])
        supply_centers = board().fixture_supply_centers(state["supplyCenters"])
        orders, answers = {}, {}
        for player, options in sorted(board().options_by_nation(state).items()):
            turn = await policies[player](position(phase, units, supply_centers, player, options))
            orders[player] = _submitted(options, turn["orders"])
            answer = {key: value for key, value in turn.items() if key != "orders"}
            if answer:
                answers[player] = answer
        outcome, state = board().outcome(state, orders)
        record = {
            "phase": phase,
            "units": units,
            "supply_centers": supply_centers,
            "orders": orders,
            "resolutions": outcome["resolutions"],
        }
        if answers:
            record["answers"] = answers
        phases.append(record)
    return {"phases": phases, "centres": centres(state), "end": end}
