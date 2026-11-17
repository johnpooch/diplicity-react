import random

from bot.core.basic import BasicBot


class BotFactory:
    def __init__(self, rng=None):
        self.rng = rng or random.Random()

    def build(self, bot, context):
        return BasicBot(context, self.rng)
