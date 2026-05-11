from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Dict, List, Optional, Tuple


class Pass:
    ARMY: ClassVar[str] = "army"
    FLEET: ClassVar[str] = "fleet"
    BOTH: ClassVar[str] = "both"


class ProvinceType:
    LAND: ClassVar[str] = "land"
    SEA: ClassVar[str] = "sea"
    COASTAL: ClassVar[str] = "coastal"


@dataclass(frozen=True)
class Adjacency:
    to: str
    pass_: str

    def allows(self, unit_type: str) -> bool:
        if unit_type == Unit.ARMY:
            return self.pass_ in (Pass.ARMY, Pass.BOTH)
        if unit_type == Unit.FLEET:
            return self.pass_ in (Pass.FLEET, Pass.BOTH)
        return False


@dataclass(frozen=True)
class Province:
    id: str
    name: str
    type: str
    supply_center: bool
    home_nation: Optional[str]
    adjacencies: Tuple[Adjacency, ...]


@dataclass(frozen=True)
class NamedCoast:
    id: str
    name: str
    parent_province: str
    adjacencies: Tuple[Adjacency, ...]


@dataclass(frozen=True)
class Nation:
    id: str
    name: str
    color: str


@dataclass(frozen=True)
class PhaseTransition:
    from_season: str
    from_type: str
    to_season: str
    to_type: str
    year_delta: int


@dataclass(frozen=True)
class PhaseProgression:
    seasons: Tuple[str, ...]
    transitions: Tuple[PhaseTransition, ...]


@dataclass(frozen=True)
class DominanceDependency:
    province: str
    nation: str


@dataclass(frozen=True)
class DominanceRule:
    province: str
    nation: str
    priority: int
    dependencies: Tuple[DominanceDependency, ...]


@dataclass(frozen=True)
class Variant:
    id: str
    name: str
    description: str
    author: str
    solo_victory_supply_centers: int
    game_ends_year: Optional[int]
    draw_after_year: Optional[int]
    rules: Optional[str]
    adjudication_modifiers: Tuple[str, ...]
    phase_progression: PhaseProgression
    nations: Tuple[Nation, ...]
    provinces: Dict[str, Province]
    named_coasts: Dict[str, NamedCoast]
    dominance_rules: Tuple[DominanceRule, ...]

    def location(self, location_id: str) -> Province:
        if location_id in self.provinces:
            return self.provinces[location_id]
        if location_id in self.named_coasts:
            return self.provinces[self.named_coasts[location_id].parent_province]
        raise KeyError(location_id)

    def adjacencies_of(self, location_id: str) -> Tuple[Adjacency, ...]:
        if location_id in self.provinces:
            return self.provinces[location_id].adjacencies
        if location_id in self.named_coasts:
            return self.named_coasts[location_id].adjacencies
        return ()

    def can_move(self, from_loc: str, to_loc: str, unit_type: str) -> bool:
        for adjacency in self.adjacencies_of(from_loc):
            if adjacency.to == to_loc:
                return adjacency.allows(unit_type)
        return False

    def parent_of(self, location_id: str) -> str:
        named = self.named_coasts.get(location_id)
        if named is not None:
            return named.parent_province
        return location_id

    def coasts_of(self, province_id: str) -> Tuple[str, ...]:
        return tuple(
            nc.id for nc in self.named_coasts.values()
            if nc.parent_province == province_id
        )

    def can_support_to(self, from_loc: str, to_loc: str, unit_type: str) -> bool:
        """
        Whether a unit at `from_loc` can support an order targeting
        `to_loc`. A supporter can support to a province by any path it
        could move to, including via any named coast of that province
        (DATC 6.B.4).
        """
        if self.can_move(from_loc, to_loc, unit_type):
            return True
        parent = self.parent_of(to_loc)
        if parent != to_loc and self.can_move(from_loc, parent, unit_type):
            return True
        target_parent = parent if parent != to_loc else to_loc
        for coast in self.coasts_of(target_parent):
            if coast == to_loc:
                continue
            if self.can_move(from_loc, coast, unit_type):
                return True
        return False

    def has_fleet_access(self, prov_id: str) -> bool:
        """
        Whether a fleet at some sea province can be adjacent to this
        province (directly or via a named coast). Inland provinces with no
        coastal access return False.
        """
        province = self.provinces.get(prov_id)
        if province is None:
            return False
        if province.type == ProvinceType.SEA:
            return True
        for adjacency in province.adjacencies:
            if adjacency.allows(Unit.FLEET):
                return True
        for named in self.named_coasts.values():
            if named.parent_province == prov_id:
                return True
        return False

    def is_convoyable(self, source: str, target: str) -> bool:
        """
        Whether `source` and `target` are both coastal-touching land
        provinces — a necessary condition for an army move between them
        to use a convoy.
        """
        target_prov = self.provinces.get(target)
        if target_prov is None or target_prov.type == ProvinceType.SEA:
            return False
        return self.has_fleet_access(source) and self.has_fleet_access(target)


@dataclass(frozen=True)
class Phase:
    season: str
    year: int
    type: str

    MOVEMENT: ClassVar[str] = "Movement"
    RETREAT: ClassVar[str] = "Retreat"
    ADJUSTMENT: ClassVar[str] = "Adjustment"


@dataclass
class Unit:
    nation: str
    type: str
    location: str
    dislodged: bool = False
    dislodged_from: Optional[str] = None

    ARMY: ClassVar[str] = "Army"
    FLEET: ClassVar[str] = "Fleet"


@dataclass
class SupplyCenter:
    nation: str
    province: str


@dataclass
class Resolution:
    province: str
    resolution: str
    reason: Optional[str] = None


@dataclass
class Outcome:
    winners: Tuple[str, ...]
    reason: str
    year: int


@dataclass
class Order:
    nation: str
    source: str
    order_type: str
    target: Optional[str] = None
    aux: Optional[str] = None
    unit_type: Optional[str] = None
    via_convoy: bool = False


@dataclass
class State:
    variant: Variant
    phase: Phase
    units: List[Unit]
    supply_centers: List[SupplyCenter]
    orders: List[Order]
    resolutions: Optional[List[Resolution]]
    skipped: bool
    outcome: Optional[Outcome]
    contested_provinces: Tuple[str, ...] = ()


@dataclass
class OrderOption:
    source: Optional[str]
    order_type: str
    target: Optional[str]
    aux: Optional[str]
    unit_type: Optional[str]
    named_coast: Optional[str]
