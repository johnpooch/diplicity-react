from bot.core.constants import BASIC_BOT_REPLY, ResponseMode
from bot.core.dumbbot.policy import select_orders
from bot.core.interfaces import Bot, Selector
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


class BasicBot(Bot):
    def __init__(self, rng):
        self.rng = rng

    def write_journal_entry(self, context: JournalContext) -> str | None:
        return None

    def plan(self, context: PlanContext) -> list[ConversationProposal]:
        return []

    def respond(self, context: ResponseContext) -> str | None:
        return BASIC_BOT_REPLY

    def respond_lightly(self, context: LightResponseContext) -> str | None:
        return BASIC_BOT_REPLY

    def choose_orders(self, context: OrdersContext) -> list[OrderOption]:
        return select_orders(context, rng=self.rng)

    def decide_draw(self, context: DrawContext) -> bool:
        return True


class BasicSelector(Selector):
    def select(self, context: SelectionContext) -> Selection | None:
        senders = {message["sender_id"] for message in context["channel"]["messages"]}
        for member_id in context["candidates"]:
            if member_id not in senders:
                return Selection(member_id=member_id, mode=ResponseMode.LIGHT)
        return None
