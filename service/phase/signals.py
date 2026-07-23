import logging
from datetime import timedelta

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from procrastinate.contrib.django import app as procrastinate_app

from common.constants import PhaseStatus
from phase.models import Phase
from phase.tasks import resolve_phase, send_deadline_warning
from phase.utils import deadline_warning_offset

logger = logging.getLogger(__name__)


_phase_pre_save_state = {}


@receiver(pre_save, sender=Phase)
def cache_phase_pre_save_state(sender, instance, **kwargs):
    if instance.pk:
        row = (
            Phase.objects.filter(pk=instance.pk)
            .values_list("scheduled_resolution", "status", "resolution_job_id", "warning_job_id")
            .first()
        )
        _phase_pre_save_state[instance.pk] = row or (None, None, None, None)


@receiver(post_save, sender=Phase)
def arm_deadline_jobs(sender, instance, created, **kwargs):
    (
        old_scheduled_resolution,
        old_status,
        old_resolution_job_id,
        old_warning_job_id,
    ) = _phase_pre_save_state.pop(instance.pk, (None, None, None, None))

    scheduled_resolution = instance.scheduled_resolution
    unchanged = (
        not created
        and instance.status == old_status
        and scheduled_resolution == old_scheduled_resolution
    )
    if unchanged:
        return

    can_arm = (
        instance.status == PhaseStatus.ACTIVE
        and scheduled_resolution is not None
        and scheduled_resolution > timezone.now()
    )

    updates = {}

    new_resolution_job_id = arm_deadline_resolution(instance, scheduled_resolution, can_arm, old_resolution_job_id)
    if new_resolution_job_id != old_resolution_job_id:
        updates["resolution_job_id"] = new_resolution_job_id

    new_warning_job_id = arm_deadline_warning(instance, scheduled_resolution, can_arm, old_warning_job_id)
    if new_warning_job_id != old_warning_job_id:
        updates["warning_job_id"] = new_warning_job_id

    if updates:
        Phase.objects.filter(pk=instance.pk).update(**updates)


def arm_deadline_resolution(instance, scheduled_resolution, can_arm, old_job_id):
    if old_job_id is not None:
        procrastinate_app.job_manager.cancel_job_by_id(old_job_id)

    if not can_arm:
        return None

    new_job_id = resolve_phase.configure(
        schedule_at=scheduled_resolution,
        lock=f"resolve-game-{instance.game_id}",
    ).defer(phase_id=instance.pk)

    logger.info(
        f"Armed deadline resolution for phase {instance.pk} (game {instance.game_id}) "
        f"at {scheduled_resolution} (job {new_job_id})"
    )
    return new_job_id


def arm_deadline_warning(instance, scheduled_resolution, can_arm, old_job_id):
    if old_job_id is not None:
        procrastinate_app.job_manager.cancel_job_by_id(old_job_id)

    if not can_arm:
        return None

    duration_seconds = instance.game.get_effective_phase_duration_seconds(instance.type)
    warning_at = scheduled_resolution - timedelta(seconds=deadline_warning_offset(duration_seconds))

    new_job_id = send_deadline_warning.configure(
        schedule_at=warning_at,
        lock=f"warn-game-{instance.game_id}",
    ).defer(phase_id=instance.pk)

    logger.info(
        f"Armed deadline warning for phase {instance.pk} (game {instance.game_id}) "
        f"at {warning_at} (job {new_job_id})"
    )
    return new_job_id
