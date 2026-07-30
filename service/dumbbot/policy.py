from common.constants import OrderType, PhaseType
from harness.exceptions import ContextError
from harness.types import Context, OrderOption
from harness.utils import current_nation

from dumbbot.board import Board
from dumbbot.exceptions import DumbbotError
from dumbbot.weights import (
    ALTERNATIVE_DIFFERENCE_MODIFIER,
    BUILD,
    FALL_MOVEMENT,
    PLAY_ALTERNATIVE,
    PROXIMITY_DEPTHS,
    REMOVE,
    SPRING_MOVEMENT,
)


def select_orders(context: Context, *, rng) -> list[OrderOption]:
    try:
        nation = current_nation(context)
    except ContextError as e:
        raise DumbbotError(str(e)) from e

    options = context["order_options"]
    if not options:
        return []

    board = Board(context, nation)
    weights = _phase_weights(context["phase"], options)
    values = _destination_values(board, weights)

    phase_type = context["phase"]["type"]
    if phase_type == PhaseType.MOVEMENT:
        return _movement_orders(board, values, options, rng)
    if phase_type == PhaseType.RETREAT:
        return _retreat_orders(board, values, options, rng)
    if any(option["order_type"] == OrderType.BUILD for option in options):
        return _build_orders(board, values, context["max_orders"], options, rng)
    return _disband_orders(board, values, context["max_orders"], options, rng)


def _phase_weights(phase, options):
    if phase["type"] == PhaseType.ADJUSTMENT:
        if any(option["order_type"] == OrderType.BUILD for option in options):
            return BUILD
        return REMOVE
    if phase["season"] == "Fall":
        return FALL_MOVEMENT
    return SPRING_MOVEMENT


def _destination_values(board, weights):
    proximity = {
        province_id: board.attack[province_id] * weights.proximity_attack
        + board.defense[province_id] * weights.proximity_defense
        for province_id in board.province_ids
    }
    proximities = [proximity]
    for _ in range(1, PROXIMITY_DEPTHS):
        previous = proximities[-1]
        current = {}
        for province_id in board.province_ids:
            contributions = sum(
                previous[board.parent[location]]
                for _, location in board.movers_into[province_id]
                if board.parent[location] != province_id
            )
            current[province_id] = (previous[province_id] + contributions) / 5.0
        proximities.append(current)

    values = {}
    for province_id in board.province_ids:
        value = sum(
            weights.proximity[depth] * proximities[depth][province_id] for depth in range(PROXIMITY_DEPTHS)
        )
        value += weights.strength * board.strength[province_id]
        value -= weights.competition * board.competition[province_id]
        value += weights.defense * board.defense[province_id]
        values[province_id] = value
    return values


def _group_by_source(options):
    grouped = {}
    for option in options:
        grouped.setdefault(option["source"], []).append(option)
    return grouped


def _destination_of(option, board):
    if option["named_coast"]:
        return board.parent[option["named_coast"]]
    if option["target"]:
        return board.parent[option["target"]]
    return option["source"]


def _find_support(options, aux, target):
    for option in options:
        if option["order_type"] == OrderType.SUPPORT and option["aux"] == aux and option["target"] == target:
            return option
    return None


def _next_item(items, value_of, rng):
    index = 0
    while index + 1 < len(items):
        current = value_of(items[index])
        following = value_of(items[index + 1])
        if current == 0:
            chance = 0
        else:
            chance = abs(current - following) * ALTERNATIVE_DIFFERENCE_MODIFIER / current
        if PLAY_ALTERNATIVE > rng.random() >= chance:
            index += 1
            continue
        break
    return items[index]


def _movement_orders(board, values, options, rng):
    grouped = _group_by_source(options)
    our_units = {
        board.parent[unit["province"]]: unit
        for unit in board.standing_units
        if unit["nation"] == board.nation
    }

    unordered = sorted(grouped)
    rng.shuffle(unordered)

    orders = {}
    moving = {}
    dependencies = {source: [] for source in grouped}

    while unordered:
        source = unordered.pop(0)
        source_options = grouped[source]
        hold = next((option for option in source_options if option["order_type"] == OrderType.HOLD), None)

        candidates = [
            option
            for option in source_options
            if option["order_type"] in (OrderType.MOVE, OrderType.MOVE_VIA_CONVOY)
            and _destination_of(option, board) not in dependencies[source]
        ]
        if hold is not None:
            candidates.append(hold)
        candidates.sort(key=lambda option: values[_destination_of(option, board)], reverse=True)

        while candidates:
            choice = _next_item(candidates, lambda option: values[_destination_of(option, board)], rng)
            destination = _destination_of(choice, board)

            if destination == source:
                orders[source] = choice
                break

            okay = True
            moves = True

            occupier = destination if destination in our_units else None
            if occupier is not None and occupier not in orders and occupier in unordered:
                unordered.insert(unordered.index(occupier) + 1, source)
                dependencies[occupier].append(source)
                break
            if occupier is not None and occupier not in moving:
                support = _find_support(source_options, occupier, occupier)
                if board.competition[occupier] > 1 and support is not None:
                    orders[source] = support
                    moves = False
                else:
                    okay = False
                    candidates.remove(choice)
                    continue

            if okay:
                mover = next((other for other, dest in moving.items() if dest == destination), None)
                if mover is not None:
                    support = _find_support(source_options, mover, destination)
                    if board.competition[destination] > 0 and support is not None:
                        orders[source] = support
                        moves = False
                    else:
                        candidates.remove(choice)
                        continue

            if moves:
                orders[source] = choice
                moving[source] = destination
            break

    return _replace_wasted_holds(board, values, grouped, orders, moving, our_units)


def _replace_wasted_holds(board, values, grouped, orders, moving, our_units):
    for source, order in orders.items():
        if order["order_type"] != OrderType.HOLD:
            continue
        unit = our_units.get(source)
        if unit is None:
            continue

        best_value = 0
        best_support = None
        for destination in board.reachable_provinces(unit["province"], unit["type"]):
            mover = next((other for other, dest in moving.items() if dest == destination), None)
            if mover is not None and board.competition[destination] > 0 and values[mover] > best_value:
                support = _find_support(grouped[source], mover, destination)
                if support is not None:
                    best_value = values[mover]
                    best_support = support
            occupier = destination if destination in orders and destination not in moving else None
            if occupier is not None and board.competition[occupier] > 1 and values[occupier] > best_value:
                support = _find_support(grouped[source], occupier, occupier)
                if support is not None:
                    best_value = values[occupier]
                    best_support = support
        if best_support is not None:
            orders[source] = best_support

    return list(orders.values())


def _retreat_orders(board, values, options, rng):
    grouped = _group_by_source(options)
    occupied = {board.parent[unit["province"]] for unit in board.standing_units}

    unordered = sorted(grouped)
    rng.shuffle(unordered)

    orders = {}
    taken = set()
    for source in unordered:
        source_options = grouped[source]
        candidates = [
            option
            for option in source_options
            if option["order_type"] in (OrderType.MOVE, OrderType.MOVE_VIA_CONVOY)
        ]
        candidates.sort(key=lambda option: values[_destination_of(option, board)], reverse=True)

        while candidates:
            choice = _next_item(candidates, lambda option: values[_destination_of(option, board)], rng)
            destination = _destination_of(choice, board)
            if destination in taken or destination in occupied:
                candidates.remove(choice)
                continue
            orders[source] = choice
            taken.add(destination)
            break
        else:
            disband = next(
                (option for option in source_options if option["order_type"] == OrderType.DISBAND), None
            )
            if disband is not None:
                orders[source] = disband

    return list(orders.values())


def _build_orders(board, values, max_orders, options, rng):
    candidates = [option for option in options if option["order_type"] == OrderType.BUILD]
    candidates.sort(key=lambda option: values[_build_site(option, board)], reverse=True)

    count = len(candidates) if max_orders is None else max_orders
    orders = {}
    while len(orders) < count and candidates:
        choice = _next_item(candidates, lambda option: values[_build_site(option, board)], rng)
        orders[choice["source"]] = choice
        candidates = [option for option in candidates if option["source"] != choice["source"]]
    return list(orders.values())


def _build_site(option, board):
    if option["named_coast"]:
        return board.parent[option["named_coast"]]
    return option["source"]


def _disband_orders(board, values, max_orders, options, rng):
    disband_by_source = {
        option["source"]: option for option in options if option["order_type"] == OrderType.DISBAND
    }
    units = [
        unit
        for unit in board.standing_units
        if unit["nation"] == board.nation and board.parent[unit["province"]] in disband_by_source
    ]
    units.sort(key=lambda unit: values[board.parent[unit["province"]]])

    count = len(disband_by_source) if max_orders is None else max_orders
    orders = {}
    while len(orders) < count and units:
        choice = _next_item(units, lambda unit: values[board.parent[unit["province"]]], rng)
        source = board.parent[choice["province"]]
        orders[source] = disband_by_source[source]
        units = [unit for unit in units if unit is not choice]
    return list(orders.values())
