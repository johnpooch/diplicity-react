from emit.context import build_context


def emit(event_type, **kwargs):
    from agent.models import AgentTask
    from channel.models import ChannelEvent
    from discord_service.dispatch import post_from_event
    from notification.models import Notification

    context = build_context(event_type, **kwargs)
    Notification.objects.create_from_event(event_type, context)
    ChannelEvent.objects.create_from_event(event_type, context)
    AgentTask.objects.create_from_event(event_type, context)
    post_from_event(event_type, context)
