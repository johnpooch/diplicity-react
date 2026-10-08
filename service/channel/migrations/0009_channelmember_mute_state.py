from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("channel", "0008_channel_event_payload"),
    ]

    operations = [
        migrations.AddField(
            model_name="channelmember",
            name="muted_indefinitely",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="channelmember",
            name="muted_until",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
