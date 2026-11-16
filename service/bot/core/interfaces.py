from abc import ABC, abstractmethod

from bot.core.types import (
    BotContext,
    ConversationProposal,
    OrderOption,
    Selection,
    SelectionContext,
)


class Bot(ABC):
    def __init__(self, context: BotContext):
        self.context = context

    @abstractmethod
    def write_journal_entry(self) -> str | None: ...

    @abstractmethod
    def plan(self) -> list[ConversationProposal]: ...

    @abstractmethod
    def respond(self, channel_id: int, mode: str) -> str | None: ...

    @abstractmethod
    def select_orders(self) -> list[OrderOption]: ...

    @abstractmethod
    def decide_draw(self) -> bool: ...


class Selector(ABC):
    @abstractmethod
    def select(self, context: SelectionContext) -> Selection | None: ...
