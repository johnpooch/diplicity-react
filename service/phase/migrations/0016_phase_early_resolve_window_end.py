from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("phase", "0015_backfill_orders_outcome"),
    ]

    operations = [
        migrations.AddField(
            model_name="phase",
            name="early_resolve_window_end",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
