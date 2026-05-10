from __future__ import annotations

from typing import List

from .domain import OrderOption, State, Variant


# === Engine ===


class Engine:
    def __init__(self, variant: Variant):
        self.variant = variant
        self.resolver = Resolver(variant)
        self.options_builder = OptionsBuilder(variant)

    def adjudicate(self, state: State) -> List[State]:
        return self.resolver.resolve(state)

    def get_options(self, state: State) -> List[OrderOption]:
        return self.options_builder.build(state)


# === Resolver ===


class Resolver:
    def __init__(self, variant: Variant):
        self.variant = variant

    def resolve(self, state: State) -> List[State]:
        return [state]


# === OptionsBuilder ===


class OptionsBuilder:
    def __init__(self, variant: Variant):
        self.variant = variant

    def build(self, state: State) -> List[OrderOption]:
        return []
