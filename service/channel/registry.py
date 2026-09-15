REGISTRY = {}


def register(event_type):
    def decorator(cls):
        cls.event_type = event_type
        REGISTRY[event_type] = cls
        return cls
    return decorator


def displayed_event_types():
    return [event_type for event_type, spec in REGISTRY.items() if spec.displayed]


class Target:
    def resolve(self, context):
        raise NotImplementedError


class PublicPress(Target):
    def resolve(self, context):
        return list(context.game.channels.filter(private=False))


class SelectedChannel(Target):
    def resolve(self, context):
        return [context.channel] if context.channel is not None else []


class ChannelEventSpec:
    event_type = None
    target = PublicPress
    displayed = False

    def get_channels(self, context):
        return self.target().resolve(context)

    def build_payload(self, context):
        return {}

    def render(self, event):
        return None


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


@register("channel_renamed")
class ChannelRenamedEvent(ChannelEventSpec):
    target = SelectedChannel
    displayed = True

    def build_payload(self, context):
        return {"nation": context.payload["nation"], "name": context.payload["name"]}

    def render(self, event):
        return f"{event.payload['nation']} renamed the channel to {event.payload['name']}"
