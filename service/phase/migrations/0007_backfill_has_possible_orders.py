# Generated manually on 2025-11-05

from django.db import migrations
from phase.utils import transform_options


def backfill_has_possible_orders(apps, schema_editor):
    PhaseState = apps.get_model("phase", "PhaseState")

    phase_states = PhaseState.objects.select_related('phase', 'member__nation').all()

    for phase_state in phase_states:
        phase = phase_state.phase

        if not phase.options:
            phase_state.has_possible_orders = False
            phase_state.save(update_fields=['has_possible_orders'])
            continue

        transformed = transform_options(phase.options)
        nation_name = phase_state.member.nation.name

        nation_options = transformed.get(nation_name, {})
        has_orders = any(province_data for province_data in nation_options.values())

        phase_state.has_possible_orders = has_orders
        phase_state.save(update_fields=['has_possible_orders'])


def reverse_backfill(apps, schema_editor):
    PhaseState = apps.get_model("phase", "PhaseState")
    PhaseState.objects.all().update(has_possible_orders=False)


class Migration(migrations.Migration):

    dependencies = [
        ('phase', '0006_phasestate_has_possible_orders'),
    ]

    operations = [
        migrations.RunPython(
            backfill_has_possible_orders,
            reverse_backfill,
        ),
    ]
