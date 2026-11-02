from discord_service.registry import get_spec
from discord_service.tasks import post


def post_from_event(event_type, context):
    spec = get_spec(event_type, context)
    if spec is None:
        return None
    return post.defer(content=spec.get_content())
