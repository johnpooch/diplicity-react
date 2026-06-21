from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0019_game_min_reliability"),
    ]

    operations = [
        migrations.AddField(
            model_name="game",
            name="accelerated_phase_window_seconds",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
