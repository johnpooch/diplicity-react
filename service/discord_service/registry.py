from django.conf import settings

from report.constants import ReportReason

REGISTRY = {}

REASON_LABELS = dict(ReportReason.REASON_CHOICES)


def register(event_type):
    def decorator(cls):
        cls.event_type = event_type
        REGISTRY[event_type] = cls
        return cls

    return decorator


def get_spec(event_type, context):
    spec_class = REGISTRY.get(event_type)
    if spec_class is None:
        return None
    return spec_class(context)


class DiscordMessageSpec:
    event_type = None

    def __init__(self, context):
        self.context = context

    def get_content(self):
        raise NotImplementedError


@register("report_opened")
class ReportOpenedSpec(DiscordMessageSpec):
    def get_content(self):
        report = self.context.payload["report"]
        reason = REASON_LABELS[report.reason]
        link = f"{settings.FRONTEND_URL}/moderation/reports/{report.id}"
        return f"New report: {reason} in {self.context.game.name}\n{link}"
