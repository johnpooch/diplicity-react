import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("channel", "0004_channelmessage_phase"),
        ("phase", "0016_phase_resolution_job_id"),
    ]

    operations = [
        migrations.CreateModel(
            name="ChannelEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("type", models.CharField(max_length=100)),
                (
                    "channel",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="events", to="channel.channel"
                    ),
                ),
                (
                    "phase",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="channel_events",
                        to="phase.phase",
                    ),
                ),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
    ]
