from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0015_backfill_game_timestamps"),
    ]

    operations = [
        migrations.AddField(
            model_name="game",
            name="non_playing_gm",
            field=models.BooleanField(default=False),
        ),
    ]
