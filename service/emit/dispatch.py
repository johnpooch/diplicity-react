from channel.models import ChannelEvent
from emit.context import build_context
from notification.models import Notification


def emit(event_type, **kwargs):
    context = build_context(event_type, **kwargs)
    Notification.objects.create_from_event(event_type, context)
    ChannelEvent.objects.create_from_event(event_type, context)
