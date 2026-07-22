from emit.audience import Explicit
from emit.link import GameLink


class EmitSpec:
    transports = []
    audience = Explicit
    link = GameLink

    def get_recipients(self, context):
        return self.audience().resolve(context)

    def get_title(self, context):
        return context.game.name

    def get_body(self, context):
        raise NotImplementedError

    def get_link(self, context):
        return self.link().resolve(context)
