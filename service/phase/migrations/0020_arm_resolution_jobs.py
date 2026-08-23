from django.db import migrations
from procrastinate.contrib.django import app as procrastinate_app


def arm_resolution_jobs(apps, schema_editor):
    Phase = apps.get_model("phase", "Phase")
    PhaseState = apps.get_model("phase", "PhaseState")
    job_manager = procrastinate_app.job_manager

    armable = list(
        Phase.objects.filter(
            status="active",
            game__sandbox=False,
            game__paused_at__isnull=True,
        )
        .exclude(game__status__in=("completed", "abandoned"))
        .values_list("id", "game_id", "scheduled_resolution", "resolution_job_id")
    )

    for phase_id, game_id, scheduled_resolution, current_job_id in armable:
        states = list(
            PhaseState.objects.filter(phase_id=phase_id).values_list(
                "has_possible_orders", "orders_confirmed"
            )
        )
        resolvable = bool(states) and all(
            confirmed for has_possible_orders, confirmed in states if has_possible_orders
        )

        should_arm = resolvable or scheduled_resolution is not None
        schedule_at = None if resolvable else scheduled_resolution

        if current_job_id is not None:
            armed = job_manager.list_jobs(id=current_job_id)
            if (
                should_arm
                and armed
                and armed[0].status == "todo"
                and armed[0].scheduled_at == schedule_at
            ):
                continue
            job_manager.cancel_job_by_id(current_job_id)

        new_job_id = None
        if should_arm:
            new_job_id = procrastinate_app.configure_task(
                "phase.resolve_phase",
                schedule_at=schedule_at,
                lock=f"resolve-game-{game_id}",
            ).defer(phase_id=phase_id)

        if new_job_id != current_job_id:
            Phase.objects.filter(pk=phase_id).update(resolution_job_id=new_job_id)


class Migration(migrations.Migration):

    dependencies = [
        ("phase", "0019_unique_live_phase_ordinal_per_game"),
        ("game", "0023_backfill_commitment_requirement"),
    ]

    operations = [
        migrations.RunPython(
            arm_resolution_jobs,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
