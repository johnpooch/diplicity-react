from django.conf import settings


class Link:
    def resolve(self, context):
        raise NotImplementedError


class NoLink(Link):
    def resolve(self, context):
        return None


class GameLink(Link):
    def resolve(self, context):
        return f"{settings.FRONTEND_URL}/game/{context.game.id}"


class ChannelLink(Link):
    def resolve(self, context):
        if context.phase is None:
            return f"{settings.FRONTEND_URL}/game/{context.game.id}"
        return (
            f"{settings.FRONTEND_URL}/game/{context.game.id}"
            f"/phase/{context.phase.id}/chat/channel/{context.channel.id}"
        )


class DrawProposalsLink(Link):
    def resolve(self, context):
        return f"{settings.FRONTEND_URL}/game/{context.game.id}/phase/{context.phase.id}/draw-proposals"
