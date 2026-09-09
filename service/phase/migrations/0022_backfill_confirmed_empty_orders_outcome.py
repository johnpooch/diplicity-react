from django.db import migrations


def backfill_confirmed_empty_orders_outcome(apps, schema_editor):
    schema_editor.execute("""
        UPDATE phase_phasestate ps
        SET orders_outcome = 'received'
        WHERE ps.orders_outcome = 'nmr'
          AND ps.has_possible_orders = TRUE
          AND ps.orders_confirmed = TRUE
          AND ps.updated_at > ps.created_at + INTERVAL '1 second'
          AND NOT EXISTS (
              SELECT 1 FROM order_order o WHERE o.phase_state_id = ps.id
          )
    """)


class Migration(migrations.Migration):

    dependencies = [
        ('phase', '0021_arm_resolution_jobs'),
        ('order', '0006_add_is_implicit_to_order'),
    ]

    operations = [
        migrations.RunPython(
            backfill_confirmed_empty_orders_outcome,
            migrations.RunPython.noop,
        ),
    ]
