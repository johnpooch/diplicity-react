from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("game", "0026_add_private_short_phase_durations"),
        ("phase", "0023_phase_warning_job_id"),
    ]

    operations = [
        AddIndexConcurrently(
            model_name="phase",
            index=models.Index(fields=["game", "-ordinal", "-id"], name="phase_latest_idx"),
        ),
        AddIndexConcurrently(
            model_name="phase",
            index=models.Index(
                condition=models.Q(("status", "completed")),
                fields=["game", "-ordinal", "-id"],
                name="phase_latest_completed_idx",
            ),
        ),
    ]
