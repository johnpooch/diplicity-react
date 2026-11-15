from abc import ABC, abstractmethod

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


class Bot(ABC):
    @abstractmethod
    def write_journal_entry(self, context: JournalContext) -> str | None: ...

    @abstractmethod
    def plan(self, context: PlanContext) -> list[ConversationProposal]: ...

    @abstractmethod
    def respond(self, context: ResponseContext) -> str | None: ...

    @abstractmethod
    def respond_lightly(self, context: LightResponseContext) -> str | None: ...

    @abstractmethod
    def choose_orders(self, context: OrdersContext) -> list[OrderOption]: ...

    @abstractmethod
    def decide_draw(self, context: DrawContext) -> bool: ...


class Selector(ABC):
    @abstractmethod
    def select(self, context: SelectionContext) -> Selection | None: ...
