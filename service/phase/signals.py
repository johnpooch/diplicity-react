import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from common.constants import PhaseStatus
from phase.models import Phase

logger = logging.getLogger(__name__)


_phase_scheduled_resolution_cache = {}


@receiver(pre_save, sender=Phase)
def cache_phase_scheduled_resolution(sender, instance, **kwargs):
    if instance.pk:
        _phase_scheduled_resolution_cache[instance.pk] = (
            Phase.objects.filter(pk=instance.pk)
            .values_list("scheduled_resolution", flat=True)
            .first()
        )


@receiver(post_save, sender=Phase)
def arm_deadline_resolution(sender, instance, created, **kwargs):
    old_scheduled_resolution = _phase_scheduled_resolution_cache.pop(instance.pk, None)

    if instance.status != PhaseStatus.ACTIVE:
        return

    scheduled_resolution = instance.scheduled_resolution
    if scheduled_resolution is None:
        return

    if not created and scheduled_resolution == old_scheduled_resolution:
        return

    if scheduled_resolution <= timezone.now():
        return

    from phase.tasks import resolve_phase

    resolve_phase.configure(
        schedule_at=scheduled_resolution,
        lock=f"resolve-game-{instance.game_id}",
    ).defer(phase_id=instance.pk)

    logger.info(
        f"Armed deadline resolution for phase {instance.pk} (game {instance.game_id}) "
        f"at {scheduled_resolution}"
    )
