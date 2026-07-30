from dataclasses import dataclass

PROXIMITY_DEPTHS = 10

SIZE_SQUARE_COEFFICIENT = 1.0
SIZE_COEFFICIENT = 4.0
SIZE_CONSTANT = 16

PLAY_ALTERNATIVE = 0.5
ALTERNATIVE_DIFFERENCE_MODIFIER = 5


@dataclass(frozen=True)
class PhaseWeights:
    proximity_attack: int
    proximity_defense: int
    proximity: tuple[int, ...]
    strength: int
    competition: int
    defense: int


SPRING_MOVEMENT = PhaseWeights(
    proximity_attack=700,
    proximity_defense=300,
    proximity=(100, 1000, 30, 10, 6, 5, 4, 3, 2, 1),
    strength=1000,
    competition=1000,
    defense=0,
)

FALL_MOVEMENT = PhaseWeights(
    proximity_attack=600,
    proximity_defense=400,
    proximity=(1000, 100, 30, 10, 6, 5, 4, 3, 2, 1),
    strength=1000,
    competition=1000,
    defense=0,
)

BUILD = PhaseWeights(
    proximity_attack=700,
    proximity_defense=300,
    proximity=(1000, 100, 30, 10, 6, 5, 4, 3, 2, 1),
    strength=0,
    competition=0,
    defense=1000,
)

REMOVE = PhaseWeights(
    proximity_attack=700,
    proximity_defense=300,
    proximity=(1000, 100, 30, 10, 6, 5, 4, 3, 2, 1),
    strength=0,
    competition=0,
    defense=1000,
)
