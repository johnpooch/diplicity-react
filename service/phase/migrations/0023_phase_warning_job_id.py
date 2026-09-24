from django.db import migrations, models
from django.utils import timezone
from procrastinate.contrib.django import app as procrastinate_app

from common.constants import DeadlineMode, DeadlineWarningJob, PhaseType, duration_to_seconds
from phase.utils import FREQUENCY_INTERVALS, deadline_warning_offset


def _duration_seconds(game, phase_type):
    if game.deadline_mode == DeadlineMode.FIXED_TIME:
        if phase_type == PhaseType.MOVEMENT:
            frequency = game.movement_frequency
        else:
            frequency = game.retreat_frequency or game.movement_frequency
        interval = FREQUENCY_INTERVALS.get(frequency) if frequency else None
        return int(interval.total_seconds()) if interval else None
    if phase_type == PhaseType.MOVEMENT:
        return duration_to_seconds(game.movement_phase_duration)
    return duration_to_seconds(game.retreat_phase_duration or game.movement_phase_duration)


def arm_warning_jobs(apps, schema_editor):
    Phase = apps.get_model("phase", "Phase")
    now = timezone.now()

    armable = (
        Phase.objects.filter(
            status="active",
            game__sandbox=False,
            game__paused_at__isnull=True,
            scheduled_resolution__isnull=False,
            warning_job_id__isnull=True,
        )
        .exclude(game__status__in=("completed", "abandoned"))
        .select_related("game")
    )

    for phase in armable:
        offset = deadline_warning_offset(_duration_seconds(phase.game, phase.type))
        schedule_at = phase.scheduled_resolution - offset
        if schedule_at <= now:
            continue
        job_id = procrastinate_app.configure_task(
            DeadlineWarningJob.TASK_NAME,
            schedule_at=schedule_at,
        ).defer(phase_id=phase.pk)
        Phase.objects.filter(pk=phase.pk).update(warning_job_id=job_id)


class Migration(migrations.Migration):

    dependencies = [
        ("phase", "0022_backfill_confirmed_empty_orders_outcome"),
        ("game", "0026_add_private_short_phase_durations"),
    ]

    operations = [
        migrations.AddField(
            model_name="phase",
            name="warning_job_id",
            field=models.BigIntegerField(blank=True, editable=False, null=True),
        ),
        migrations.RunPython(
            arm_warning_jobs,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
