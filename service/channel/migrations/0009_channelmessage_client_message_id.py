from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("channel", "0008_channel_event_payload"),
    ]

    operations = [
        migrations.AddField(
            model_name="channelmessage",
            name="client_message_id",
            field=models.UUIDField(blank=True, null=True),
        ),
    ]
