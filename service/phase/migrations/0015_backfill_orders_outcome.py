from django.db import migrations


def backfill_orders_outcome(apps, schema_editor):
    schema_editor.execute("""
        UPDATE phase_phasestate ps
        SET orders_outcome = 'received'
        FROM phase_phase pp
        WHERE ps.phase_id = pp.id
          AND pp.status = 'completed'
          AND ps.has_possible_orders = TRUE
          AND ps.orders_outcome IS NULL
          AND EXISTS (
              SELECT 1 FROM order_order o WHERE o.phase_state_id = ps.id
          )
    """)
    schema_editor.execute("""
        UPDATE phase_phasestate ps
        SET orders_outcome = 'nmr'
        FROM phase_phase pp
        WHERE ps.phase_id = pp.id
          AND pp.status = 'completed'
          AND ps.has_possible_orders = TRUE
          AND ps.orders_outcome IS NULL
          AND NOT EXISTS (
              SELECT 1 FROM order_order o WHERE o.phase_state_id = ps.id
          )
    """)


def reverse_backfill(apps, schema_editor):
    schema_editor.execute("UPDATE phase_phasestate SET orders_outcome = NULL WHERE orders_outcome IS NOT NULL")


class Migration(migrations.Migration):

    dependencies = [
        ('phase', '0014_phasestate_orders_outcome'),
        ('order', '0006_add_is_implicit_to_order'),
    ]

    operations = [
        migrations.RunPython(
            backfill_orders_outcome,
            reverse_backfill,
        ),
    ]
