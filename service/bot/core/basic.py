from bot.core.constants import BASIC_BOT_REPLY, ResponseMode
from bot.core.dumbbot.policy import select_orders
from bot.core.interfaces import Bot, Selector
from bot.core.types import (
    BotContext,
    ConversationProposal,
    OrderOption,
    Selection,
    SelectionContext,
)


class BasicBot(Bot):
    def __init__(self, context: BotContext, rng):
        super().__init__(context)
        self.rng = rng

    def write_journal_entry(self) -> str | None:
        return None

    def plan(self) -> list[ConversationProposal]:
        return []

    def respond(self, channel_id: int, mode: str) -> str | None:
        return BASIC_BOT_REPLY

    def select_orders(self) -> list[OrderOption]:
        return select_orders(self.context, rng=self.rng)

    def decide_draw(self) -> bool:
        return True


class BasicSelector(Selector):
    def select(self, context: SelectionContext) -> Selection | None:
        senders = {message["sender_id"] for message in context["channel"]["messages"]}
        for member_id in context["candidates"]:
            if member_id not in senders:
                return Selection(member_id=member_id, mode=ResponseMode.LIGHT)
        return None
