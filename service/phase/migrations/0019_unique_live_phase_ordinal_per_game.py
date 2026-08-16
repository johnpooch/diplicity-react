from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("phase", "0018_complete_phases_of_finished_games"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="phase",
            options={"ordering": ["ordinal", "id"]},
        ),
        migrations.AddConstraint(
            model_name="phase",
            constraint=models.UniqueConstraint(
                condition=models.Q(("status", "completed"), _negated=True),
                fields=("game", "ordinal"),
                name="unique_live_phase_ordinal_per_game",
            ),
        ),
    ]
