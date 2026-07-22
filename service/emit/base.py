from emit.audience import Explicit
from emit.context import EmitContext
from emit.link import GameLink


class EmitSpec:
    event_type = None
    transports = []
    audience = Explicit
    link = GameLink

    def build_context(self, game=None, phase=None, actor=None, channel=None, **payload):
        if game is None and phase is not None:
            game = phase.game
        return EmitContext(self.event_type, game, phase, actor, channel, payload)

    def get_recipients(self, context):
        return self.audience().resolve(context)

    def get_title(self, context):
        return context.game.name

    def get_body(self, context):
        raise NotImplementedError

    def get_link(self, context):
        return self.link().resolve(context)

    def get_email_subject(self, context):
        return context.game.name

    def actor_name(self, context):
        if context.game.anonymity_active:
            return "Anonymous"
        actor = context.actor
        return actor.profile.name if actor is not None else "Deleted User"
