from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0025_game_muster_deadline_game_muster_job_id_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="game",
            name="movement_phase_duration",
            field=models.CharField(
                blank=True,
                choices=[
                    ("5 minutes", "5 minutes"),
                    ("15 minutes", "15 minutes"),
                    ("30 minutes", "30 minutes"),
                    ("1 hour", "1 hour"),
                    ("2 hours", "2 hours"),
                    ("4 hours", "4 hours"),
                    ("8 hours", "8 hours"),
                    ("12 hours", "12 hours"),
                    ("24 hours", "24 hours"),
                    ("48 hours", "48 hours"),
                    ("3 days", "3 days"),
                    ("4 days", "4 days"),
                    ("1 week", "1 week"),
                    ("2 weeks", "2 weeks"),
                ],
                default="24 hours",
                max_length=20,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="game",
            name="retreat_phase_duration",
            field=models.CharField(
                blank=True,
                choices=[
                    ("5 minutes", "5 minutes"),
                    ("15 minutes", "15 minutes"),
                    ("30 minutes", "30 minutes"),
                    ("1 hour", "1 hour"),
                    ("2 hours", "2 hours"),
                    ("4 hours", "4 hours"),
                    ("8 hours", "8 hours"),
                    ("12 hours", "12 hours"),
                    ("24 hours", "24 hours"),
                    ("48 hours", "48 hours"),
                    ("3 days", "3 days"),
                    ("4 days", "4 days"),
                    ("1 week", "1 week"),
                    ("2 weeks", "2 weeks"),
                ],
                max_length=20,
                null=True,
            ),
        ),
    ]
