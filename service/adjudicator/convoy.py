"""Convoy path-finding.

Owns the graph search that determines whether a chain of sea provinces
connects an army's source coast to its target coast. Path-finding is
*not* the same as convoy success — a path may exist on paper but be
disrupted at resolution time if any fleet in the path is dislodged.
This module answers the static question; C3 will integrate the dynamic
question into the Decision graph.

Public symbols: `convoy_path_exists`, `convoy_path_through_fleet`,
`is_convoy_redundant`, and `fleet_reaches_coast`. Everything else is
module-private.
"""
from __future__ import annotations

from typing import Collection, Optional, Set

from .domain import Unit
from .types import StateView


def convoy_path_exists(
    state: StateView,
    army_source: str,
    army_target: str,
    convoying_fleet_locations: Collection[str],
) -> bool:
    """Return True iff there exists a chain of sea-adjacent locations
    starting at a fleet-passable neighbour of `army_source`, ending at
    a fleet-passable neighbour of `army_target`, where every interior
    node is one of `convoying_fleet_locations`.

    `army_source` and `army_target` are parent province ids — convoy
    endpoints. The function does not require the army to be present
    at the source; it answers the geometric question only. Callers
    are responsible for unit-presence and order-matching checks.

    `convoying_fleet_locations` is the set of fleet locations whose
    ConvoyOrders match this army's move. Locations may be parent
    province ids or (rarely, variant-dependent) sea-province ids; the
    function treats them uniformly via `parent_of`. An empty collection
    is taken to mean "no convoying-fleet restriction" — the function
    then returns True iff some sea province sits adjacent to both
    endpoints; C2/C3 will layer the 'at least one matched convoy fleet'
    requirement on top.

    Implementation: BFS over the variant's adjacency graph, restricted
    to sea provinces in the convoying set (plus the two endpoints'
    sea-passable neighbours as entry/exit). Cost: O(V + E) over the
    sea sub-graph. Memoization is not done here — callers that need
    repeated queries are expected to wrap calls or maintain their own
    cache (C3 will do this inside the Decision graph)."""
    if army_source == army_target:
        return False
    variant = state.variant()
    start_set = _sea_neighbours(state, army_source)
    end_set = _sea_neighbours(state, army_target)
    if not convoying_fleet_locations:
        return bool(start_set & end_set)
    allowed_interior: Set[str] = {
        variant.parent_of(loc) for loc in convoying_fleet_locations
    }
    visited: Set[str] = set()
    frontier: Set[str] = start_set & allowed_interior
    while frontier:
        next_frontier: Set[str] = set()
        for node in frontier:
            if node in visited:
                continue
            visited.add(node)
            if node in end_set:
                return True
            for adjacency in variant.adjacencies_of(node):
                if not adjacency.allows(Unit.FLEET):
                    continue
                neighbour = variant.parent_of(adjacency.to)
                if not state.province(neighbour).is_sea():
                    continue
                if neighbour in visited:
                    continue
                if neighbour in allowed_interior:
                    next_frontier.add(neighbour)
        frontier = next_frontier
    return False


def convoy_path_through_fleet(
    state: StateView,
    army_source: str,
    army_target: str,
    fleet_location: str,
    convoying_fleet_locations: Collection[str],
) -> bool:
    """Return True iff a convoy chain from `army_source` to `army_target`
    through `convoying_fleet_locations` exists that the fleet at
    `fleet_location` is actually part of.

    `convoy_path_exists` answers whether *some* chain connects the two
    coasts; this answers the stricter question godip's option generator
    needs — whether a chain exists that this specific fleet is on
    (godip's `ConvoyPathFinder` path-finds from the convoying fleet's
    own location). A chain A→B through F exists iff F is reachable from
    `army_source` and `army_target` is reachable from F, both restricted
    to the given on-board fleet set."""
    if army_source == army_target:
        return False
    variant = state.variant()
    fleet_parent = variant.parent_of(fleet_location)
    if not state.province(fleet_parent).is_sea():
        return False
    allowed_interior: Set[str] = {
        variant.parent_of(loc) for loc in convoying_fleet_locations
    }
    if fleet_parent not in allowed_interior:
        return False
    return _sea_chain_connects(
        state, _sea_neighbours(state, army_source), {fleet_parent}, allowed_interior
    ) and _sea_chain_connects(
        state, {fleet_parent}, _sea_neighbours(state, army_target), allowed_interior
    )


def _sea_chain_connects(
    state: StateView,
    start_set: Set[str],
    end_set: Set[str],
    allowed_interior: Set[str],
) -> bool:
    """BFS over fleet-passable sea adjacency: True iff some node in
    `end_set` is reachable from `start_set`, with every visited node
    constrained to `allowed_interior`. Only nodes in `allowed_interior`
    are ever checked against `end_set`, matching `convoy_path_exists` —
    the first and last sea province in a convoy chain must each hold a
    convoying fleet."""
    visited: Set[str] = set()
    frontier: Set[str] = start_set & allowed_interior
    variant = state.variant()
    while frontier:
        next_frontier: Set[str] = set()
        for node in frontier:
            if node in visited:
                continue
            visited.add(node)
            if node in end_set:
                return True
            for adjacency in variant.adjacencies_of(node):
                if not adjacency.allows(Unit.FLEET):
                    continue
                neighbour = variant.parent_of(adjacency.to)
                if neighbour in visited:
                    continue
                if not state.province(neighbour).is_sea():
                    continue
                if neighbour in allowed_interior:
                    next_frontier.add(neighbour)
        frontier = next_frontier
    return False


def is_convoy_redundant(
    state: StateView,
    fleet_location: str,
    army_source: str,
    army_target: str,
    candidate_fleet_locations: Collection[str],
) -> bool:
    """Return True iff the convoy at `fleet_location` is on a longer-than-
    minimum chain through the given candidate fleets (DATC 6.G.19,
    6.F.12). The candidate set is all submitted matching ConvoyOrders'
    fleet locations including this one.

    A fleet is redundant only when it sits on some chain *and* every
    chain it's on is longer than the shortest chain available. A fleet
    on no chain at all is not redundant — the order simply expresses
    intent that doesn't help (DATC 6.G.6)."""
    variant = state.variant()
    candidate_parents = {
        variant.parent_of(loc) for loc in candidate_fleet_locations
    }
    fleet_parent = variant.parent_of(fleet_location)
    if fleet_parent not in candidate_parents:
        return False
    start_set = _sea_neighbours(state, army_source)
    end_set = _sea_neighbours(state, army_target)
    min_total = _min_chain_length(state, start_set, end_set, candidate_parents)
    if min_total is None:
        return False
    d_from = _min_distance(state, start_set, fleet_parent, candidate_parents)
    d_to = _min_distance(state, {fleet_parent}, end_set, candidate_parents)
    if d_from is None or d_to is None:
        return False
    return d_from + d_to - 1 > min_total


def _min_chain_length(
    state: StateView,
    start_set: Set[str],
    end_set: Set[str],
    candidates: Set[str],
) -> Optional[int]:
    """BFS shortest path from any node in start_set ∩ candidates to any
    node in end_set, through nodes in candidates, with edges following
    fleet-passable sea adjacency. Length is in fleets along the chain."""
    visited: Set[str] = set()
    frontier: Set[str] = start_set & candidates
    if not frontier:
        return None
    depth = 1
    visited |= frontier
    if frontier & end_set:
        return depth
    variant = state.variant()
    while frontier:
        depth += 1
        next_frontier: Set[str] = set()
        for sea in frontier:
            for adjacency in variant.adjacencies_of(sea):
                if not adjacency.allows(Unit.FLEET):
                    continue
                neighbour = variant.parent_of(adjacency.to)
                if neighbour in visited:
                    continue
                if neighbour not in candidates:
                    continue
                if not state.province(neighbour).is_sea():
                    continue
                visited.add(neighbour)
                next_frontier.add(neighbour)
        if next_frontier & end_set:
            return depth
        frontier = next_frontier
    return None


def _min_distance(
    state: StateView,
    start_set: Set[str],
    target: object,
    candidates: Set[str],
) -> Optional[int]:
    """BFS shortest path from any node in start_set ∩ candidates to the
    given target, through candidates. Target may be either a single
    province id (str) or a set of province ids; the search terminates
    when any node in the target set is first visited. Distance counts
    fleets (the start node counts as 1)."""
    if isinstance(target, str):
        target_set: Set[str] = {target}
    else:
        target_set = set(target)
    visited: Set[str] = set()
    frontier: Set[str] = start_set & candidates
    if not frontier:
        return None
    depth = 1
    visited |= frontier
    if frontier & target_set:
        return depth
    variant = state.variant()
    while frontier:
        depth += 1
        next_frontier: Set[str] = set()
        for sea in frontier:
            for adjacency in variant.adjacencies_of(sea):
                if not adjacency.allows(Unit.FLEET):
                    continue
                neighbour = variant.parent_of(adjacency.to)
                if neighbour in visited:
                    continue
                if neighbour not in candidates:
                    continue
                if not state.province(neighbour).is_sea():
                    continue
                visited.add(neighbour)
                next_frontier.add(neighbour)
        if next_frontier & target_set:
            return depth
        frontier = next_frontier
    return None


def fleet_reaches_coast(
    state: StateView, fleet_location: str, coast_location: str
) -> bool:
    """Return True iff a fleet at `fleet_location` is topologically
    capable of reaching `coast_location` via a chain of sea provinces
    in the variant graph (independent of any orders or other units).

    Used by ConvoyFleetReachesEndpointsCheck to reject convoy fleets
    that cannot possibly be on any chain for the convoy's endpoints
    (DATC 6.G.7). Both endpoints of the convoy must be reachable for
    the fleet to participate.

    The fleet's own province counts as a starting node only when it is
    a sea province (named coasts and coastal fleet locations cannot
    convoy)."""
    variant = state.variant()
    fleet_parent = variant.parent_of(fleet_location)
    if not state.province(fleet_parent).is_sea():
        return False
    if fleet_parent in _sea_neighbours(state, coast_location):
        return True
    visited: Set[str] = {fleet_parent}
    frontier: Set[str] = {fleet_parent}
    target_neighbours = _sea_neighbours(state, coast_location)
    while frontier:
        next_frontier: Set[str] = set()
        for sea in frontier:
            for adjacency in variant.adjacencies_of(sea):
                if not adjacency.allows(Unit.FLEET):
                    continue
                neighbour = variant.parent_of(adjacency.to)
                if neighbour in visited:
                    continue
                if not state.province(neighbour).is_sea():
                    continue
                if neighbour in target_neighbours:
                    return True
                visited.add(neighbour)
                next_frontier.add(neighbour)
        frontier = next_frontier
    return False


def _sea_neighbours(state: StateView, location: str) -> Set[str]:
    """The set of sea-province parent ids reachable from `location` by a
    single fleet-passable adjacency. Used as the entry/exit set for the
    convoy BFS: a fleet can pick up or set down an army at any sea
    province adjacent to that army's coast via a fleet-passable edge.

    When `location` is a province with named coasts (e.g. bul, spa), the
    sea adjacencies live on the named coasts rather than the parent —
    so we union over the parent and every named coast belonging to it.

    Additionally, for `convoyable_capable` provinces (e.g. Gibraltar),
    include their fleet-passable adjacencies even if they are not coastal.
    """
    variant = state.variant()
    result: Set[str] = set()
    parent = variant.parent_of(location)
    locations_to_check = [parent, *variant.coasts_of(parent)]
    for loc in locations_to_check:
        for adjacency in variant.adjacencies_of(loc):
            if not adjacency.allows(Unit.FLEET):
                continue
            adj_parent = variant.parent_of(adjacency.to)
            if state.province(adj_parent).is_sea():
                result.add(adj_parent)
    # Also check convoyable_capable provinces that are not coastal
    prov = variant.provinces.get(parent)
    if prov is not None and prov.convoyable_capable and not prov.type == "coastal":
        # It's a convoyable_capable province that is not coastal (e.g., Gibraltar as sea space)
        # Check its adjacencies for fleet-passable sea connections
        for adjacency in variant.adjacencies_of(parent):
            if not adjacency.allows(Unit.FLEET):
                continue
            adj_parent = variant.parent_of(adjacency.to)
            if state.province(adj_parent).is_sea():
                result.add(adj_parent)
    return result
