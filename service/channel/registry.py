REGISTRY = {}


def register(event_type):
    def decorator(cls):
        cls.event_type = event_type
        REGISTRY[event_type] = cls
        return cls
    return decorator


class Target:
    def resolve(self, context):
        raise NotImplementedError


class PublicPress(Target):
    def resolve(self, context):
        return list(context.game.channels.filter(private=False))


class ChannelEventSpec:
    event_type = None
    target = PublicPress

    def get_channels(self, context):
        return self.target().resolve(context)


@register("game_start")
class GameStartEvent(ChannelEventSpec):
    pass


@register("game_draw")
class GameDrawEvent(ChannelEventSpec):
    pass


@register("game_solo_win")
class GameSoloWinEvent(ChannelEventSpec):
    pass


@register("game_solo_loss")
class GameSoloLossEvent(ChannelEventSpec):
    pass


@register("phase_resolved")
class PhaseResolvedEvent(ChannelEventSpec):
    pass


@register("phase_resolved_early")
class PhaseResolvedEarlyEvent(ChannelEventSpec):
    pass


@register("game_admin_reassigned")
class GameAdminReassignedEvent(ChannelEventSpec):
    pass


@register("game_paused")
class GamePausedEvent(ChannelEventSpec):
    pass


@register("game_resumed")
class GameResumedEvent(ChannelEventSpec):
    pass


@register("game_deadline_extended")
class GameDeadlineExtendedEvent(ChannelEventSpec):
    pass


@register("civil_disorder")
class CivilDisorderEvent(ChannelEventSpec):
    pass


@register("civil_disorder_recovery")
class CivilDisorderRecoveryEvent(ChannelEventSpec):
    pass


@register("elimination")
class EliminationEvent(ChannelEventSpec):
    pass


@register("nmr_extension_applied")
class NmrExtensionAppliedEvent(ChannelEventSpec):
    pass
