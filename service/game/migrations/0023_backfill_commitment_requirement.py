from django.db import migrations


def backfill_commitment_requirement(apps, schema_editor):
    Game = apps.get_model("game", "Game")
    Game.objects.filter(min_reliability="reliable_only").update(
        commitment_requirement="committed"
    )


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0022_game_commitment_requirement"),
    ]

    operations = [
        migrations.RunPython(backfill_commitment_requirement, migrations.RunPython.noop),
    ]
