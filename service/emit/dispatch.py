from emit.context import build_context


def emit(event_type, **kwargs):
    from channel.models import ChannelEvent
    from notification.models import Notification

    context = build_context(event_type, **kwargs)
    Notification.objects.create_from_event(event_type, context)
    ChannelEvent.objects.create_from_event(event_type, context)
