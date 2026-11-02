from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("report", "0003_report_assigned_to"),
    ]

    operations = [
        AddIndexConcurrently(
            model_name="report",
            index=models.Index(fields=["assigned_to"], name="report_assigned_to_idx"),
        ),
    ]
