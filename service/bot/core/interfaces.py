from typing import Protocol

from bot.core.types import (
    ConversationProposal,
    DrawContext,
    JournalContext,
    LightResponseContext,
    OrderOption,
    OrdersContext,
    PlanContext,
    ResponseContext,
    Selection,
    SelectionContext,
)


class Bot(Protocol):
    def write_journal_entry(self, context: JournalContext) -> str | None: ...

    def plan(self, context: PlanContext) -> list[ConversationProposal]: ...

    def respond(self, context: ResponseContext) -> str | None: ...

    def respond_lightly(self, context: LightResponseContext) -> str | None: ...

    def choose_orders(self, context: OrdersContext) -> list[OrderOption]: ...

    def decide_draw(self, context: DrawContext) -> bool: ...


class Selector(Protocol):
    def select(self, context: SelectionContext) -> Selection | None: ...
