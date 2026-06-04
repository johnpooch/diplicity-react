from django.db import migrations
from django.db.models import Count


def backfill_orders_outcome(apps, schema_editor):
    PhaseState = apps.get_model("phase", "PhaseState")

    base_qs = PhaseState.objects.filter(
        phase__status="completed",
        has_possible_orders=True,
    ).annotate(order_count=Count("orders"))

    CHUNK = 1000
    for outcome, qs in [
        ("received", base_qs.filter(order_count__gt=0)),
        ("nmr", base_qs.filter(order_count=0)),
    ]:
        ids = []
        for ps_id in qs.values_list("id", flat=True).iterator():
            ids.append(ps_id)
            if len(ids) >= CHUNK:
                PhaseState.objects.filter(id__in=ids).update(orders_outcome=outcome)
                ids = []
        if ids:
            PhaseState.objects.filter(id__in=ids).update(orders_outcome=outcome)


def reverse_backfill(apps, schema_editor):
    PhaseState = apps.get_model("phase", "PhaseState")
    PhaseState.objects.update(orders_outcome=None)


class Migration(migrations.Migration):

    dependencies = [
        ('phase', '0014_phasestate_orders_outcome'),
    ]

    operations = [
        migrations.RunPython(
            backfill_orders_outcome,
            reverse_backfill,
        ),
    ]
