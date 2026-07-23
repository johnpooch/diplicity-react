from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("phase", "0016_phase_resolution_job_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="phase",
            name="warning_job_id",
            field=models.BigIntegerField(blank=True, editable=False, null=True),
        ),
        migrations.RemoveField(
            model_name="phasestate",
            name="deadline_warning_sent_for",
        ),
    ]
