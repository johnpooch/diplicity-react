"""Movement-phase strength-and-cut resolver.

This module owns the only iterative inner loop in the adjudicator. Every
other reducer in `engine.py` is a single-pass pure transformation;
strength resolution genuinely is not — support cuts, attack/defense/
prevent/hold strengths, and Move statuses form a graph of mutually-
dependent unknowns. The eight-category model in CLAUDE.md fits
single-pass transformations; it fits this problem awkwardly. Pulling the
solver out of `engine.py` makes that paradigm split explicit instead
of hiding it inside one reducer's helpers.

The internal representation is an explicit Decision graph:

  * Every unresolved question — "what is the support_cut for order i?",
    "what is the attack_strength of move i?", "what is the move_status
    of move i?" — is a `_Decision` keyed by `(kind, subject)`.
  * Each decision lists, up front, the other decisions it reads from.
    Dependencies are static — known from `parsed_orders` plus the
    ILLEGAL marks set by earlier reducers.
  * A work queue holds decisions whose dependencies are all resolved.
    Popping one computes its value and re-checks every decision that
    depends on it; newly-ready ones are enqueued.
  * When the queue empties but decisions remain, we look for closed
    dependency cycles. Two kinds get resolved:

      - Clean N-move cycles (A→B→C→A): if every member's attack
        strictly exceeds every external competitor's prevent, all
        members succeed (DATC 6.F.4).

      - Convoy paradoxes (Szykman's rule): cycles in the dependency
        graph that involve at least one `_CONVOY_PATH_INTACT`
        decision are broken by forcing all such decisions in the
        cycle to False, disrupting the relevant convoys (DATC
        Szykman's rule, 6.F.13ff). This matches the modern
        adjudication consensus.

    Cycles that match neither shape are unresolvable in the current
    solver and will exhaust the `_MAX_CYCLE_PASSES` cap, raising
    `RuntimeError`. Such cycles should not arise from valid
    Diplomacy positions; if one does, it indicates a solver bug.
  * Cycle-resolution passes are capped at `_MAX_CYCLE_PASSES`; exceeding
    that cap raises `RuntimeError` — the disciplined replacement for
    the legacy `MAX_ITERATIONS` guard.

The boundary with `StateView` stays pure: a `StateView` goes in once,
a `StateView` comes out once. The decision dict is mutated inside the
solver — that is local state, not part of the engine's frozen
`AdjudicationState`.

The module's only public symbol is `resolve_strengths_and_cuts`. The
adaptor reducer in `engine.py` (`ResolveStrengthsAndCutsReducer`)
calls this function and nothing else.

Future scope: alternative paradox-resolution rules (the all-hold
rule, DPTG) could plug in alongside Szykman as additional
cycle-breaker methods following the same pattern. The
Decision-graph substrate accommodates them without further
architectural change.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, replace
from typing import (
    Deque,
    Dict,
    FrozenSet,
    List,
    Optional,
    Set,
    Tuple,
)

from .convoy import convoy_path_exists
from .types import (
    ConvoyOrder,
    HoldOrder,
    MoveOrder,
    Order,
    OrderResolution,
    Status,
    StateView,
    SupportHoldOrder,
    SupportMoveOrder,
)


# === Decision kind constants ===

_SUPPORT_CUT = "support_cut"
_ATTACK_STRENGTH = "attack_strength"
_DEFENSE_STRENGTH = "defense_strength"
_PREVENT_STRENGTH = "prevent_strength"
_HOLD_STRENGTH = "hold_strength"
_MOVE_STATUS = "move_status"
_CONVOY_PATH_INTACT = "convoy_path_intact"


_Key = Tuple[str, int]


# === Decision dataclass ===


@dataclass(frozen=True)
class _Decision:
    """One unresolved question in the strength resolution.

    `kind` is one of the module-level kind constants. `subject` is the
    `parsed_orders` index the decision is about. `value` is `None` while
    unresolved; once decided, it holds the per-kind answer (a `Status`
    string for `support_cut`, an `int` for the strength kinds, or a
    `(status, failure_reason)` tuple for `move_status`). `dependencies`
    is the set of other decision keys this one reads from — computed
    statically when the decision is enumerated.
    """

    kind: str
    subject: int
    value: Optional[object] = None
    dependencies: FrozenSet[_Key] = frozenset()


# === Public entry point ===


def resolve_strengths_and_cuts(state: StateView) -> StateView:
    """Resolve Movement-phase contests: support cuts, attack / defense /
    prevent / hold strengths, and Move order statuses.

    Pure function: returns a new `StateView` with the resolution fields
    populated on every `OrderResolution` for which they apply. Does not
    mutate the input state.

    The solver is required to produce a value for every decision it
    constructs. If the decision graph terminates with any unresolved
    decisions, `resolve_strengths_and_cuts` raises `RuntimeError` —
    defaulting unresolved values to plausible answers would mask solver
    bugs and produce silently-incorrect adjudications. Decisions that
    are "not applicable" to a given order (e.g. defense_strength for a
    non-head-to-head move) must not be created in the first place;
    "unresolved" and "not applicable" are not the same state.
    """
    return _Solver(state).solve()


# === Solver ===


class _Solver:
    """Drives the Decision graph from enumeration to final projection.

    Instance state — decisions, dependents, the ready queue — is local
    to one solve() call. The `StateView` is held read-only; the only
    state-producing call is the final `_project_back` that constructs
    a new `StateView` via `state.replace(...)`.
    """

    _MAX_CYCLE_PASSES = 8

    def __init__(self, state: StateView) -> None:
        self._state = state
        self._parsed: Tuple[Order, ...] = state.parsed_orders()
        self._initial_resolutions: Tuple[OrderResolution, ...] = state.resolutions()
        self._variant = state.variant()
        self._decisions: Dict[_Key, _Decision] = {}
        self._dependents: Dict[_Key, Set[_Key]] = {}
        self._ready: Deque[_Key] = deque()

    def solve(self) -> StateView:
        self._enumerate_decisions()
        self._build_dependents_and_initial_ready()
        passes = 0
        while True:
            self._drain_ready_queue()
            if self._all_resolved():
                break
            if self._try_speculative_move_status():
                passes += 1
                if passes > self._MAX_CYCLE_PASSES:
                    raise RuntimeError("Decision graph did not converge")
                continue
            if self._try_resolve_clean_cycles():
                passes += 1
                if passes > self._MAX_CYCLE_PASSES:
                    raise RuntimeError("Decision graph did not converge")
                continue
            if self._try_resolve_szykman_paradoxes():
                passes += 1
                if passes > self._MAX_CYCLE_PASSES:
                    raise RuntimeError("Decision graph did not converge")
                continue
            break
        self._assert_decisions_complete()
        return self._project_back()

    # --- Decision enumeration ---

    def _enumerate_decisions(self) -> None:
        resolutions = self._initial_resolutions
        for i, order in enumerate(self._parsed):
            illegal = resolutions[i].status == Status.ILLEGAL
            if isinstance(order, (SupportHoldOrder, SupportMoveOrder)):
                if not illegal:
                    self._add_decision(
                        _SUPPORT_CUT, i, self._support_cut_deps(i)
                    )
                self._add_decision(
                    _HOLD_STRENGTH, i, self._hold_strength_deps(i, illegal)
                )
                continue
            if isinstance(order, MoveOrder):
                if not illegal:
                    self._add_decision(
                        _ATTACK_STRENGTH, i, self._attack_strength_deps(i)
                    )
                    if _head_to_head_opponent_index(self._state, i) is not None:
                        self._add_decision(
                            _DEFENSE_STRENGTH, i, self._defense_strength_deps(i)
                        )
                    self._add_decision(
                        _PREVENT_STRENGTH, i, self._prevent_strength_deps(i)
                    )
                    if resolutions[i].via_convoy:
                        self._add_decision(
                            _CONVOY_PATH_INTACT,
                            i,
                            self._convoy_path_intact_deps(i),
                        )
                    self._add_decision(
                        _MOVE_STATUS, i, self._move_status_deps(i)
                    )
                self._add_decision(
                    _HOLD_STRENGTH, i, self._hold_strength_deps(i, illegal)
                )
                continue
            if isinstance(order, (HoldOrder, ConvoyOrder)):
                self._add_decision(
                    _HOLD_STRENGTH, i, self._hold_strength_deps(i, illegal)
                )

    def _add_decision(
        self, kind: str, subject: int, dependencies: FrozenSet[_Key]
    ) -> None:
        self._decisions[(kind, subject)] = _Decision(
            kind=kind, subject=subject, dependencies=dependencies
        )

    # --- Dependency rules ---

    def _support_cut_deps(self, i: int) -> FrozenSet[_Key]:
        """A Support is normally cut by any non-own-nation attack on the
        supporter. Two conditional dependencies layer on top:

          - cut-exception attacker (DATC 6.D.4): an attack from the
            province the SupportMove targets does not cut — unless it
            dislodges the supporter (DATC 6.D.17). Reads MOVE_STATUS of
            that attacker.
          - convoyed attacker (DATC 6.F.6): a convoyed attack with a
            broken convoy never happens and so does not cut. Reads
            CONVOY_PATH_INTACT of that attacker.

        SupportHold has no cut exception but is still subject to the
        convoy rule. Decisions whose dependencies are absent in a given
        position are simply resolved cheaply."""
        order = self._parsed[i]
        if not isinstance(order, (SupportHoldOrder, SupportMoveOrder)):
            return frozenset()
        variant = self._variant
        resolutions = self._initial_resolutions
        supporter_parent = variant.parent_of(order.source)
        cut_exception_parent: Optional[str] = None
        if isinstance(order, SupportMoveOrder):
            cut_exception_parent = variant.parent_of(order.target)
        deps: Set[_Key] = set()
        for j, attacker in enumerate(self._parsed):
            if not isinstance(attacker, MoveOrder):
                continue
            if resolutions[j].status == Status.ILLEGAL:
                continue
            if variant.parent_of(attacker.target) != supporter_parent:
                continue
            if attacker.nation == order.nation:
                continue
            if (
                cut_exception_parent is not None
                and variant.parent_of(attacker.source) == cut_exception_parent
            ):
                deps.add((_MOVE_STATUS, j))
            if resolutions[j].via_convoy:
                deps.add((_CONVOY_PATH_INTACT, j))
        return frozenset(deps)

    def _attack_strength_deps(self, i: int) -> FrozenSet[_Key]:
        supports = _matching_attack_supports(self._state, i)
        deps: Set[_Key] = set((_SUPPORT_CUT, k) for k in supports)
        # In h2h, the opponent is the defender — its nation is known up
        # front, no MOVE_STATUS dep needed (and adding one would cycle
        # via the symmetric ATTACK_STRENGTH).
        if _head_to_head_opponent_index(self._state, i) is not None:
            return frozenset(deps)
        defender_idx = _defender_order_index(self._state, i)
        if defender_idx is None:
            return frozenset(deps)
        defender_order = self._parsed[defender_idx]
        if not (
            isinstance(defender_order, MoveOrder)
            and self._initial_resolutions[defender_idx].status != Status.ILLEGAL
        ):
            return frozenset(deps)
        # Only matters when at least one of our supports is from the
        # defender's static nation — that's the support that would be
        # filtered out by the own-nation rule unless the defender
        # actually vacates (DATC 6.D.10/12). Without such a support
        # we don't need MOVE_STATUS[defender] at all.
        defender_nation = defender_order.nation
        if any(self._parsed[k].nation == defender_nation for k in supports):
            deps.add((_MOVE_STATUS, defender_idx))
        return frozenset(deps)

    def _defense_strength_deps(self, i: int) -> FrozenSet[_Key]:
        return frozenset(
            (_SUPPORT_CUT, k) for k in _matching_attack_supports(self._state, i)
        )

    def _prevent_strength_deps(self, i: int) -> FrozenSet[_Key]:
        deps: Set[_Key] = set(
            (_SUPPORT_CUT, k) for k in _matching_attack_supports(self._state, i)
        )
        h2h = _head_to_head_opponent_index(self._state, i)
        if h2h is not None:
            deps.add((_MOVE_STATUS, h2h))
        # A convoyed move with a broken convoy never happens and so
        # exerts no prevent strength (DATC 6.F.8). The decision
        # therefore reads CONVOY_PATH_INTACT[i] when relevant.
        if self._initial_resolutions[i].via_convoy:
            deps.add((_CONVOY_PATH_INTACT, i))
        return frozenset(deps)

    def _move_status_deps(self, i: int) -> FrozenSet[_Key]:
        parsed = self._parsed
        variant = self._variant
        resolutions = self._initial_resolutions
        order = parsed[i]
        assert isinstance(order, MoveOrder)
        deps: Set[_Key] = {(_ATTACK_STRENGTH, i)}
        if resolutions[i].via_convoy:
            deps.add((_CONVOY_PATH_INTACT, i))
        target_parent = variant.parent_of(order.target)
        for j, other in enumerate(parsed):
            if j == i:
                continue
            if not isinstance(other, MoveOrder):
                continue
            if resolutions[j].status == Status.ILLEGAL:
                continue
            if variant.parent_of(other.target) != target_parent:
                continue
            deps.add((_PREVENT_STRENGTH, j))
        h2h = _head_to_head_opponent_index(self._state, i)
        if h2h is not None:
            deps.add((_DEFENSE_STRENGTH, h2h))
            return frozenset(deps)
        defender_idx = _defender_order_index(self._state, i)
        if defender_idx is not None:
            deps.add((_HOLD_STRENGTH, defender_idx))
            defender_order = parsed[defender_idx]
            if (
                isinstance(defender_order, MoveOrder)
                and resolutions[defender_idx].status != Status.ILLEGAL
            ):
                deps.add((_MOVE_STATUS, defender_idx))
        return frozenset(deps)

    def _convoy_path_intact_deps(self, i: int) -> FrozenSet[_Key]:
        """`_CONVOY_PATH_INTACT[i]` depends on `_MOVE_STATUS[j]` for every
        Move `j` that targets the parent province of some matched
        ConvoyOrder for Move `i`. Knowing those outcomes tells us which
        of the convoy fleets are dislodged."""
        fleet_parents = self._matched_convoy_fleet_parents(i)
        deps: Set[_Key] = set()
        variant = self._variant
        resolutions = self._initial_resolutions
        for j, other in enumerate(self._parsed):
            if not isinstance(other, MoveOrder):
                continue
            if resolutions[j].status == Status.ILLEGAL:
                continue
            if variant.parent_of(other.target) in fleet_parents:
                deps.add((_MOVE_STATUS, j))
        return frozenset(deps)

    def _matched_convoy_fleet_parents(self, move_index: int) -> Set[str]:
        """Parent provinces of fleets whose matched, non-ILLEGAL
        ConvoyOrders correspond to the given convoyed Move (by source-
        target endpoint match). Fleet *locations* are sea provinces;
        their parent is the same province (sea provinces have no
        separate named coasts). Returns parents for set-membership
        convenience."""
        move = self._parsed[move_index]
        assert isinstance(move, MoveOrder)
        variant = self._variant
        resolutions = self._initial_resolutions
        source_parent = variant.parent_of(move.source)
        target_parent = variant.parent_of(move.target)
        parents: Set[str] = set()
        for k, order in enumerate(self._parsed):
            if not isinstance(order, ConvoyOrder):
                continue
            r = resolutions[k]
            if r.status == Status.ILLEGAL:
                continue
            if not r.convoy_matched:
                continue
            if variant.parent_of(order.army_source) != source_parent:
                continue
            if variant.parent_of(order.army_target) != target_parent:
                continue
            parents.add(variant.parent_of(order.source))
        return parents

    def _matched_convoy_fleet_locations(
        self, move_index: int
    ) -> Tuple[str, ...]:
        """Fleet locations (not parents) of matched, non-ILLEGAL
        ConvoyOrders corresponding to the given convoyed Move. The
        locations are passed to convoy_path_exists, which normalises via
        parent_of internally."""
        move = self._parsed[move_index]
        assert isinstance(move, MoveOrder)
        variant = self._variant
        resolutions = self._initial_resolutions
        source_parent = variant.parent_of(move.source)
        target_parent = variant.parent_of(move.target)
        results: List[str] = []
        for k, order in enumerate(self._parsed):
            if not isinstance(order, ConvoyOrder):
                continue
            r = resolutions[k]
            if r.status == Status.ILLEGAL:
                continue
            if not r.convoy_matched:
                continue
            if variant.parent_of(order.army_source) != source_parent:
                continue
            if variant.parent_of(order.army_target) != target_parent:
                continue
            results.append(order.source)
        return tuple(results)

    def _hold_strength_deps(self, i: int, illegal: bool) -> FrozenSet[_Key]:
        order = self._parsed[i]
        if isinstance(order, MoveOrder) and not illegal:
            return frozenset({(_MOVE_STATUS, i)})
        return frozenset(
            (_SUPPORT_CUT, k) for k in _matching_hold_supports(self._state, i)
        )

    # --- Work queue plumbing ---

    def _build_dependents_and_initial_ready(self) -> None:
        for key, decision in self._decisions.items():
            for dep_key in decision.dependencies:
                self._dependents.setdefault(dep_key, set()).add(key)
            if not decision.dependencies:
                self._ready.append(key)

    def _drain_ready_queue(self) -> None:
        while self._ready:
            key = self._ready.popleft()
            decision = self._decisions[key]
            if decision.value is not None:
                continue
            if not self._all_deps_resolved(decision):
                continue
            value = self._compute(key)
            if value is None:
                continue
            self._decisions[key] = replace(decision, value=value)
            self._enqueue_dependents(key)

    def _enqueue_dependents(self, key: _Key) -> None:
        for dep_key in self._dependents.get(key, ()):
            dep = self._decisions[dep_key]
            if dep.value is not None:
                continue
            if self._all_deps_resolved(dep):
                self._ready.append(dep_key)

    def _all_deps_resolved(self, decision: _Decision) -> bool:
        for d in decision.dependencies:
            if self._decisions[d].value is None:
                return False
        return True

    def _all_resolved(self) -> bool:
        return all(d.value is not None for d in self._decisions.values())

    # --- Compute dispatch ---

    def _compute(self, key: _Key) -> Optional[object]:
        kind, idx = key
        if kind == _SUPPORT_CUT:
            return self._compute_support_cut(idx)
        if kind == _ATTACK_STRENGTH:
            return self._compute_attack_strength(idx)
        if kind == _DEFENSE_STRENGTH:
            return self._compute_defense_strength(idx)
        if kind == _PREVENT_STRENGTH:
            return self._compute_prevent_strength(idx)
        if kind == _HOLD_STRENGTH:
            return self._compute_hold_strength(idx)
        if kind == _MOVE_STATUS:
            return self._compute_move_status(idx)
        if kind == _CONVOY_PATH_INTACT:
            return self._compute_convoy_path_intact(idx)
        raise RuntimeError(f"Unknown decision kind: {kind!r}")

    def _dec_value(self, key: _Key) -> Optional[object]:
        decision = self._decisions.get(key)
        if decision is None:
            return None
        return decision.value

    # --- Per-kind compute functions (DATC strength rules: 6.D, 6.E, 6.G) ---

    def _compute_support_cut(self, i: int) -> Optional[str]:
        parsed = self._parsed
        resolutions = self._initial_resolutions
        variant = self._variant
        order = parsed[i]
        assert isinstance(order, (SupportHoldOrder, SupportMoveOrder))
        supporter_parent = variant.parent_of(order.source)
        cut_exception_parent: Optional[str] = None
        if isinstance(order, SupportMoveOrder):
            cut_exception_parent = variant.parent_of(order.target)
        for j, attacker in enumerate(parsed):
            if not isinstance(attacker, MoveOrder):
                continue
            if resolutions[j].status == Status.ILLEGAL:
                continue
            if variant.parent_of(attacker.target) != supporter_parent:
                continue
            if attacker.nation == order.nation:
                continue
            if resolutions[j].via_convoy:
                # Convoyed attacker: only cuts if its convoy is intact
                # (DATC 6.F.6 — a dislodged convoy doesn't cut support).
                intact = self._dec_value((_CONVOY_PATH_INTACT, j))
                if intact is None:
                    return None
                if not intact:
                    continue
            if (
                cut_exception_parent is not None
                and variant.parent_of(attacker.source) == cut_exception_parent
            ):
                # Cut-exception attacker: doesn't cut unless it actually
                # dislodges the supporter (DATC 6.D.17).
                attacker_status = self._dec_value((_MOVE_STATUS, j))
                if attacker_status is None:
                    return None
                if attacker_status[0] == Status.OK:
                    return Status.CUT
                continue
            return Status.CUT
        return Status.OK

    def _compute_attack_strength(self, i: int) -> Optional[int]:
        defender_nation = self._effective_defender_nation_for(i)
        supports = _matching_attack_supports(self._state, i)
        parsed = self._parsed
        resolutions = self._initial_resolutions
        active = 0
        for k in supports:
            if not resolutions[k].support_matched:
                continue
            if self._dec_value((_SUPPORT_CUT, k)) != Status.OK:
                continue
            if defender_nation is not None and parsed[k].nation == defender_nation:
                continue
            active += 1
        return 1 + active

    def _compute_defense_strength(self, i: int) -> int:
        supports = _matching_attack_supports(self._state, i)
        resolutions = self._initial_resolutions
        active = 0
        for k in supports:
            if not resolutions[k].support_matched:
                continue
            if self._dec_value((_SUPPORT_CUT, k)) != Status.OK:
                continue
            active += 1
        return 1 + active

    def _compute_prevent_strength(self, i: int) -> Optional[int]:
        if self._initial_resolutions[i].via_convoy:
            intact = self._dec_value((_CONVOY_PATH_INTACT, i))
            if intact is None:
                return None
            if not intact:
                return 0
        h2h = _head_to_head_opponent_index(self._state, i)
        if h2h is not None:
            opp_value = self._dec_value((_MOVE_STATUS, h2h))
            if opp_value is not None and opp_value[0] == Status.OK:
                return 0
        supports = _matching_attack_supports(self._state, i)
        resolutions = self._initial_resolutions
        active = 0
        for k in supports:
            if not resolutions[k].support_matched:
                continue
            if self._dec_value((_SUPPORT_CUT, k)) != Status.OK:
                continue
            active += 1
        return 1 + active

    def _compute_hold_strength(self, i: int) -> Optional[int]:
        order = self._parsed[i]
        initial_status = self._initial_resolutions[i].status
        if isinstance(order, MoveOrder) and initial_status != Status.ILLEGAL:
            move_value = self._dec_value((_MOVE_STATUS, i))
            if move_value is None:
                return None
            if move_value[0] == Status.OK:
                return 0
            return 1
        supports = _matching_hold_supports(self._state, i)
        resolutions = self._initial_resolutions
        active = 0
        for k in supports:
            if not resolutions[k].support_matched:
                continue
            if self._dec_value((_SUPPORT_CUT, k)) != Status.OK:
                continue
            active += 1
        return 1 + active

    def _compute_move_status(
        self, i: int
    ) -> Optional[Tuple[str, Optional[str]]]:
        parsed = self._parsed
        variant = self._variant
        resolutions = self._initial_resolutions
        order = parsed[i]
        assert isinstance(order, MoveOrder)
        attack = self._dec_value((_ATTACK_STRENGTH, i))
        if attack is None:
            return None
        if resolutions[i].via_convoy:
            intact = self._dec_value((_CONVOY_PATH_INTACT, i))
            if intact is None:
                return None
            if not intact:
                return (
                    Status.BOUNCE,
                    "The convoy was disrupted.",
                )
        target_parent = variant.parent_of(order.target)
        max_prevent = 0
        for j, other in enumerate(parsed):
            if j == i:
                continue
            if not isinstance(other, MoveOrder):
                continue
            if resolutions[j].status == Status.ILLEGAL:
                continue
            if variant.parent_of(other.target) != target_parent:
                continue
            prev = self._dec_value((_PREVENT_STRENGTH, j))
            if prev is None:
                return None
            if prev > max_prevent:
                max_prevent = prev
        if attack <= max_prevent:
            return (
                Status.BOUNCE,
                "The attack was prevented by a competing move of equal or greater strength.",
            )
        h2h_index = _head_to_head_opponent_index(self._state, i)
        if h2h_index is not None:
            opp_defense = self._dec_value((_DEFENSE_STRENGTH, h2h_index))
            if opp_defense is None:
                return None
            if attack <= opp_defense:
                return (
                    Status.BOUNCE,
                    "The head-to-head attack failed to overpower the opposing unit.",
                )
            opponent = parsed[h2h_index]
            assert isinstance(opponent, MoveOrder)
            if opponent.nation == order.nation:
                return (
                    Status.BOUNCE,
                    "A unit cannot dislodge a unit of its own nation.",
                )
            return (Status.OK, None)
        defender_idx = _defender_order_index(self._state, i)
        if defender_idx is None:
            return (Status.OK, None)
        defender_order = parsed[defender_idx]
        defender_initial_status = resolutions[defender_idx].status
        if (
            isinstance(defender_order, MoveOrder)
            and defender_initial_status != Status.ILLEGAL
        ):
            defender_value = self._dec_value((_MOVE_STATUS, defender_idx))
            if defender_value is None:
                return None
            defender_status = defender_value[0]
        else:
            defender_status = defender_initial_status
        if isinstance(defender_order, MoveOrder) and defender_status == Status.OK:
            return (Status.OK, None)
        hold = self._dec_value((_HOLD_STRENGTH, defender_idx))
        if hold is None:
            return None
        if attack <= hold:
            return (
                Status.BOUNCE,
                "The attack was not strong enough to dislodge the defender.",
            )
        if defender_order.nation == order.nation:
            return (
                Status.BOUNCE,
                "A unit cannot dislodge a unit of its own nation.",
            )
        return (Status.OK, None)

    def _compute_convoy_path_intact(self, i: int) -> Optional[bool]:
        """Three-valued convoy path: True if a chain through known-alive
        fleets already works; False if no chain works even through all
        potentially-alive fleets; None otherwise. Mirrors v1's
        ConvoyPathDecision (DATC convoy paradox handling). The three-
        valued return is what enables the multi-route paradox to settle
        without a Szykman fallback (DATC 6.F.19/20): if an alternate
        route is known-intact, the main convoy is definitely intact and
        downstream support cuts apply normally."""
        move = self._parsed[i]
        assert isinstance(move, MoveOrder)
        variant = self._variant
        parsed = self._parsed
        source_parent = variant.parent_of(move.source)
        target_parent = variant.parent_of(move.target)
        matched_fleet_locs = self._matched_convoy_fleet_locations(i)
        definitely_alive: List[str] = []
        candidates: List[str] = []
        for fleet_loc in matched_fleet_locs:
            fleet_parent = variant.parent_of(fleet_loc)
            any_ok_attacker = False
            any_unknown_attacker = False
            for j, other in enumerate(parsed):
                if not isinstance(other, MoveOrder):
                    continue
                if variant.parent_of(other.target) != fleet_parent:
                    continue
                if self._initial_resolutions[j].status == Status.ILLEGAL:
                    continue
                status_value = self._dec_value((_MOVE_STATUS, j))
                if status_value is None:
                    any_unknown_attacker = True
                elif status_value[0] == Status.OK:
                    any_ok_attacker = True
            if any_ok_attacker:
                continue
            candidates.append(fleet_loc)
            if not any_unknown_attacker:
                definitely_alive.append(fleet_loc)
        if definitely_alive and convoy_path_exists(
            self._state, source_parent, target_parent, tuple(definitely_alive)
        ):
            return True
        if not candidates:
            return False
        if not convoy_path_exists(
            self._state, source_parent, target_parent, tuple(candidates)
        ):
            return False
        return None

    def _defender_nation_for(self, i: int) -> Optional[str]:
        h2h = _head_to_head_opponent_index(self._state, i)
        if h2h is not None:
            return self._parsed[h2h].nation
        defender_idx = _defender_order_index(self._state, i)
        if defender_idx is None:
            return None
        return self._parsed[defender_idx].nation

    def _effective_defender_nation_for(self, i: int) -> Optional[str]:
        """Nation of the defender that would actually be dislodged if this
        attack succeeds. Returns None when no unit will remain at the
        target — either the province is empty, or the unit currently
        there is a Move that resolves OK and vacates. The own-nation
        support exclusion in attack-strength computation uses this
        effective view, not the static occupant (DATC 6.D.10/12)."""
        h2h = _head_to_head_opponent_index(self._state, i)
        if h2h is not None:
            return self._parsed[h2h].nation
        defender_idx = _defender_order_index(self._state, i)
        if defender_idx is None:
            return None
        defender_order = self._parsed[defender_idx]
        defender_status = self._initial_resolutions[defender_idx].status
        if isinstance(defender_order, MoveOrder) and defender_status != Status.ILLEGAL:
            move_status = self._dec_value((_MOVE_STATUS, defender_idx))
            if move_status is not None and move_status[0] == Status.OK:
                return None
        return defender_order.nation

    # --- Speculative MOVE_STATUS compute (cycle short-circuit) ---

    def _try_speculative_move_status(self) -> bool:
        """For each unresolved MOVE_STATUS or CONVOY_PATH_INTACT decision,
        run its compute even though the declared dependencies aren't all
        resolved. Both compute functions are conservative — they return
        None unless they can decide from currently-known information
        (MOVE_STATUS via attack-vs-prevent short-circuit; CONVOY_PATH_INTACT
        via three-valued path enumeration). Any value they return is
        derived only from already-resolved decisions, so committing it
        is correctness-preserving.

        This breaks the move-cycle stall in DATC 6.C.3 (one cycle member
        decidable directly cascades the rest) and the multi-route
        convoy-paradox stall in DATC 6.F.19/20 (an alternate convoy
        route's known-intact status decides the support cut without
        needing to enter the paradox)."""
        changed = False
        for key, decision in list(self._decisions.items()):
            if key[0] not in (_MOVE_STATUS, _CONVOY_PATH_INTACT):
                continue
            if decision.value is not None:
                continue
            value = self._compute(key)
            if value is None:
                continue
            self._decisions[key] = replace(decision, value=value)
            self._enqueue_dependents(key)
            changed = True
        return changed

    # --- Cycle detection (DATC 6.F.4 clean N-cycles) ---

    def _try_resolve_clean_cycles(self) -> bool:
        parsed = self._parsed
        variant = self._variant
        moves_by_source_parent: Dict[str, int] = {}
        for i, order in enumerate(parsed):
            if not isinstance(order, MoveOrder):
                continue
            if self._dec_value((_MOVE_STATUS, i)) is not None:
                continue
            if self._initial_resolutions[i].status == Status.ILLEGAL:
                continue
            moves_by_source_parent[variant.parent_of(order.source)] = i
        changed = False
        seen_in_resolved_cycle: Set[int] = set()
        for i, order in enumerate(parsed):
            if not isinstance(order, MoveOrder):
                continue
            if self._initial_resolutions[i].status == Status.ILLEGAL:
                continue
            if self._dec_value((_MOVE_STATUS, i)) is not None:
                continue
            if i in seen_in_resolved_cycle:
                continue
            cycle = self._trace_cycle(i, moves_by_source_parent)
            if cycle is None:
                continue
            if not self._cycle_is_clean(cycle):
                continue
            for j in cycle:
                key = (_MOVE_STATUS, j)
                self._decisions[key] = replace(
                    self._decisions[key], value=(Status.OK, None)
                )
                seen_in_resolved_cycle.add(j)
                self._enqueue_dependents(key)
            changed = True
        return changed

    def _trace_cycle(
        self, start_index: int, moves_by_source_parent: Dict[str, int]
    ) -> Optional[List[int]]:
        parsed = self._parsed
        variant = self._variant
        chain = [start_index]
        seen = {variant.parent_of(parsed[start_index].source)}
        current = start_index
        while True:
            order = parsed[current]
            assert isinstance(order, MoveOrder)
            nxt = moves_by_source_parent.get(variant.parent_of(order.target))
            if nxt is None:
                return None
            nxt_parent = variant.parent_of(parsed[nxt].source)
            if nxt == start_index:
                return chain
            if nxt_parent in seen:
                return None
            chain.append(nxt)
            seen.add(nxt_parent)
            current = nxt

    def _cycle_is_clean(self, cycle: List[int]) -> bool:
        parsed = self._parsed
        variant = self._variant
        resolutions = self._initial_resolutions
        cycle_set: Set[int] = set(cycle)
        for member_idx in cycle:
            member = parsed[member_idx]
            assert isinstance(member, MoveOrder)
            attack = self._dec_value((_ATTACK_STRENGTH, member_idx))
            if attack is None:
                # In swap cycles (each member's defender is itself a
                # cycle member that vacates), ATTACK can stall on a
                # cyclic MOVE_STATUS dependency. Recompute optimistically
                # treating cycle-member defenders as having no effective
                # nation — the standard DATC reading of cycle/swap
                # outcomes (DATC 6.C.1, 6.G.1).
                attack = self._cycle_optimistic_attack(member_idx, cycle_set)
                if attack is None:
                    return False
            target_parent = variant.parent_of(member.target)
            for j, other in enumerate(parsed):
                if j == member_idx:
                    continue
                if not isinstance(other, MoveOrder):
                    continue
                if resolutions[j].status == Status.ILLEGAL:
                    continue
                if variant.parent_of(other.target) != target_parent:
                    continue
                prev = self._dec_value((_PREVENT_STRENGTH, j))
                if prev is None or attack <= prev:
                    return False
        return True

    def _cycle_optimistic_attack(
        self, i: int, cycle_set: Set[int]
    ) -> Optional[int]:
        """Compute ATTACK_STRENGTH[i] under the assumption that every
        defender that is itself a member of `cycle_set` succeeds and
        vacates. Returns None when a non-cycle dependency is still
        unresolved."""
        supports = _matching_attack_supports(self._state, i)
        for k in supports:
            if self._dec_value((_SUPPORT_CUT, k)) is None:
                return None
        h2h = _head_to_head_opponent_index(self._state, i)
        if h2h is not None:
            defender_nation: Optional[str] = self._parsed[h2h].nation
        else:
            defender_idx = _defender_order_index(self._state, i)
            defender_nation = None
            if defender_idx is not None and defender_idx not in cycle_set:
                defender_order = self._parsed[defender_idx]
                defender_status = self._initial_resolutions[defender_idx].status
                if (
                    isinstance(defender_order, MoveOrder)
                    and defender_status != Status.ILLEGAL
                ):
                    move_status = self._dec_value((_MOVE_STATUS, defender_idx))
                    if move_status is None:
                        return None
                    if move_status[0] != Status.OK:
                        defender_nation = defender_order.nation
                else:
                    defender_nation = defender_order.nation
        active = 0
        resolutions = self._initial_resolutions
        for k in supports:
            if not resolutions[k].support_matched:
                continue
            if self._dec_value((_SUPPORT_CUT, k)) != Status.OK:
                continue
            if defender_nation is not None and self._parsed[k].nation == defender_nation:
                continue
            active += 1
        return 1 + active

    # --- Szykman's rule (DATC 6.F.13ff convoy paradoxes) ---

    def _try_resolve_szykman_paradoxes(self) -> bool:
        """Detect dependency cycles among unresolved decisions and break
        any cycle containing at least one `_CONVOY_PATH_INTACT` by
        forcing those decisions to False (DATC Szykman's rule: convoyed
        moves in a paradox are treated as disrupted).

        Returns True iff at least one decision value was forced. The
        solver's main loop relies on the True return to know the
        dependency graph state has changed and is worth re-processing.

        Cycles without any `_CONVOY_PATH_INTACT` are not broken here.
        They should not arise in practice; if one does, the main loop
        will exhaust `_MAX_CYCLE_PASSES` and raise — the right
        behavior, since a non-convoy paradox cycle indicates a solver
        bug rather than a recognised paradox shape.
        """
        cycle = self._find_unresolved_cycle()
        if cycle is None:
            return False
        convoy_decisions_in_cycle = [
            key for key in cycle if key[0] == _CONVOY_PATH_INTACT
        ]
        if not convoy_decisions_in_cycle:
            return False
        for key in convoy_decisions_in_cycle:
            decision = self._decisions[key]
            self._decisions[key] = replace(decision, value=False)
            self._enqueue_dependents(key)
        return True

    def _find_unresolved_cycle(self) -> Optional[List[_Key]]:
        """Return any one cycle of unresolved decisions in the
        dependency graph, or None if no cycle exists. Iterative DFS
        with three colors:
          - white: not yet visited
          - gray: currently on the DFS stack
          - black: fully explored, no cycle through this node

        A back-edge from the current node to a gray node indicates a
        cycle; the cycle members are extracted by walking the DFS
        stack from the cycle's entry point onward."""
        WHITE, GRAY, BLACK = 0, 1, 2
        color: Dict[_Key, int] = {
            key: WHITE
            for key, d in self._decisions.items()
            if d.value is None
        }
        for start in list(color):
            if color[start] != WHITE:
                continue
            stack: List[Tuple[_Key, Deque[_Key]]] = [
                (start, deque(self._unresolved_deps(start)))
            ]
            color[start] = GRAY
            while stack:
                node, remaining = stack[-1]
                if not remaining:
                    color[node] = BLACK
                    stack.pop()
                    continue
                neighbour = remaining.popleft()
                if neighbour not in color:
                    continue
                if color[neighbour] == BLACK:
                    continue
                if color[neighbour] == GRAY:
                    return self._extract_cycle(neighbour, stack)
                color[neighbour] = GRAY
                stack.append(
                    (neighbour, deque(self._unresolved_deps(neighbour)))
                )
        return None

    def _unresolved_deps(self, key: _Key) -> List[_Key]:
        """Dependencies of `key` that are themselves still unresolved.
        Resolved deps are not part of any active cycle, so they are
        filtered out before DFS — both for correctness (a resolved
        node cannot complete a cycle of unresolved values) and to
        keep the search tight."""
        decision = self._decisions[key]
        return [
            d for d in decision.dependencies
            if self._decisions[d].value is None
        ]

    def _extract_cycle(
        self,
        cycle_entry: _Key,
        stack: List[Tuple[_Key, Deque[_Key]]],
    ) -> List[_Key]:
        """Reconstruct the cycle from the DFS stack: the slice from
        `cycle_entry` (the gray node we found a back-edge to) through
        the current top-of-stack node."""
        cycle_members: List[_Key] = []
        found_entry = False
        for node, _ in stack:
            if node == cycle_entry:
                found_entry = True
            if found_entry:
                cycle_members.append(node)
        return cycle_members

    # --- Completeness check ---

    def _assert_decisions_complete(self) -> None:
        unresolved = [
            (key, decision)
            for key, decision in self._decisions.items()
            if decision.value is None
        ]
        if not unresolved:
            return
        formatted = ", ".join(
            f"{kind}[{subject}]" for (kind, subject), _ in unresolved
        )
        raise RuntimeError(
            "Strength-and-cut solver terminated with unresolved decisions: "
            f"{formatted}. This indicates a bug in the decision graph "
            "construction or the cycle breaker."
        )

    # --- Project the resolved decisions back into a new StateView ---

    def _project_back(self) -> StateView:
        resolutions = list(self._initial_resolutions)
        for (kind, idx), decision in self._decisions.items():
            value = decision.value
            if value is None:
                continue
            r = resolutions[idx]
            if kind == _SUPPORT_CUT:
                r = replace(r, support_cut=value)
            elif kind == _ATTACK_STRENGTH:
                r = replace(r, attack_strength=value)
            elif kind == _DEFENSE_STRENGTH:
                r = replace(r, defense_strength=value)
            elif kind == _PREVENT_STRENGTH:
                r = replace(r, prevent_strength=value)
            elif kind == _HOLD_STRENGTH:
                r = replace(r, hold_strength=value)
            elif kind == _MOVE_STATUS:
                status, reason = value
                r = replace(r, status=status, failure_reason=reason)
            elif kind == _CONVOY_PATH_INTACT:
                r = replace(r, convoy_path_intact=value)
            resolutions[idx] = r
        return self._state.replace(resolutions=tuple(resolutions))


# === Geometry helpers (module-private) ===
#
# Read-only questions about parsed orders + the variant adjacency. These
# are not methods on Views because they belong to the solver, not to the
# engine's view layer — they encode strength-resolution geometry, not
# general queries about state. P3 will revisit `source_province()` as a
# narrow exception on Order; until then, these stay as functions.


def _matching_attack_supports(
    state: StateView, move_index: int
) -> Tuple[int, ...]:
    """Indices of SupportMoveOrders matched to the given Move."""
    parsed = state.parsed_orders()
    resolutions = state.resolutions()
    variant = state.variant()
    move = parsed[move_index]
    assert isinstance(move, MoveOrder)
    results: List[int] = []
    for k, support in enumerate(parsed):
        if not isinstance(support, SupportMoveOrder):
            continue
        if resolutions[k].status == Status.ILLEGAL:
            continue
        if not resolutions[k].support_matched:
            continue
        if variant.parent_of(support.supported_source) != variant.parent_of(
            move.source
        ):
            continue
        if support.target != move.target and variant.parent_of(
            support.target
        ) != variant.parent_of(move.target):
            continue
        results.append(k)
    return tuple(results)


def _matching_hold_supports(
    state: StateView, supported_index: int
) -> Tuple[int, ...]:
    """Indices of SupportHoldOrders matched to the unit at
    parsed_orders[supported_index]'s source province."""
    parsed = state.parsed_orders()
    resolutions = state.resolutions()
    variant = state.variant()
    supported = parsed[supported_index]
    supported_parent = variant.parent_of(supported.source)
    results: List[int] = []
    for k, support in enumerate(parsed):
        if not isinstance(support, SupportHoldOrder):
            continue
        if resolutions[k].status == Status.ILLEGAL:
            continue
        if not resolutions[k].support_matched:
            continue
        if variant.parent_of(support.supported_source) != supported_parent:
            continue
        results.append(k)
    return tuple(results)


def _head_to_head_opponent_index(
    state: StateView, move_index: int
) -> Optional[int]:
    """Index of the opposing MoveOrder forming a head-to-head pair with
    parsed_orders[move_index], or None. Two Moves are head-to-head when
    each targets the other's source parent and neither is ILLEGAL — *and
    neither moves by convoy* (DATC 6.G: convoyed moves do not form
    head-to-head pairs)."""
    parsed = state.parsed_orders()
    resolutions = state.resolutions()
    variant = state.variant()
    move = parsed[move_index]
    assert isinstance(move, MoveOrder)
    if resolutions[move_index].via_convoy:
        return None
    target_parent = variant.parent_of(move.target)
    source_parent = variant.parent_of(move.source)
    for j, other in enumerate(parsed):
        if j == move_index:
            continue
        if not isinstance(other, MoveOrder):
            continue
        if resolutions[j].status == Status.ILLEGAL:
            continue
        if resolutions[j].via_convoy:
            continue
        if variant.parent_of(other.source) != target_parent:
            continue
        if variant.parent_of(other.target) != source_parent:
            continue
        return j
    return None


def _defender_order_index(
    state: StateView, attacker_index: int
) -> Optional[int]:
    """Index of the Movement-phase order at the attacker's target parent
    (the unit being attacked), or None. Returned regardless of order
    type — the caller checks whether that unit is moving away. Convoy
    orders are included so attacks on convoying fleets resolve against
    the fleet's hold strength rather than as if the province were
    empty."""
    parsed = state.parsed_orders()
    variant = state.variant()
    attacker = parsed[attacker_index]
    assert isinstance(attacker, MoveOrder)
    target_parent = variant.parent_of(attacker.target)
    for i, order in enumerate(parsed):
        if not isinstance(
            order,
            (
                HoldOrder,
                MoveOrder,
                SupportHoldOrder,
                SupportMoveOrder,
                ConvoyOrder,
            ),
        ):
            continue
        if variant.parent_of(order.source) == target_parent:
            return i
    return None
