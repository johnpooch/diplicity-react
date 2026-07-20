import functools

from common.constants import PhaseStatus
from phase.models import Phase

_previous_phase_status = {}


def capture_phase_status(sender, instance, **kwargs):
    if instance.pk:
        _previous_phase_status[instance.pk] = (
            Phase.objects.filter(pk=instance.pk).values_list("status", flat=True).first()
        )


def on_phase_resolved(func):
    @functools.wraps(func)
    def wrapper(sender, instance, created, **kwargs):
        previous_status = _previous_phase_status.pop(instance.pk, None)
        if previous_status == PhaseStatus.ACTIVE and instance.status == PhaseStatus.COMPLETED:
            return func(sender=sender, instance=instance, created=created, **kwargs)

    return wrapper
