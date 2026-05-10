from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


PASS_ARMY = "army"
PASS_FLEET = "fleet"
PASS_BOTH = "both"

PROVINCE_LAND = "land"
PROVINCE_SEA = "sea"
PROVINCE_COASTAL = "coastal"

UNIT_ARMY = "Army"
UNIT_FLEET = "Fleet"

PHASE_MOVEMENT = "Movement"
PHASE_RETREAT = "Retreat"
PHASE_ADJUSTMENT = "Adjustment"


@dataclass(frozen=True)
class Adjacency:
    to: str
    pass_: str


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


@dataclass(frozen=True)
class Phase:
    season: str
    year: int
    type: str


@dataclass
class Unit:
    nation: str
    type: str
    location: str
    dislodged: bool = False


@dataclass
class SupplyCenter:
    nation: str
    province: str


@dataclass
class Resolution:
    province: str
    resolution: str


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


@dataclass
class OrderOption:
    source: Optional[str]
    order_type: str
    target: Optional[str]
    aux: Optional[str]
    unit_type: Optional[str]
    named_coast: Optional[str]
