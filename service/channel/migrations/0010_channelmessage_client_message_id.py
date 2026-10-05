from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("channel", "0009_channelmember_mute_state"),
    ]

    operations = [
        migrations.AddField(
            model_name="channelmessage",
            name="client_message_id",
            field=models.UUIDField(blank=True, null=True),
        ),
    ]
