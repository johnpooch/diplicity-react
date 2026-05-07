from django.db import migrations


def backfill(apps, schema_editor):
    from user_profile.utils import backfill_reliability_data

    backfill_reliability_data()


class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0003_add_reliability_counters'),
        ('member', '0005_add_outcome_state'),
        ('phase', '0010_add_youngstown_redux_template_phase'),
        ('order', '0005_alter_orderresolution_status'),
        ('unit', '0007_add_youngstown_redux_units'),
        ('game', '0012_add_press_type_field'),
    ]

    operations = [
        migrations.RunPython(backfill, reverse_code=migrations.RunPython.noop),
    ]
