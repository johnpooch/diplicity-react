from django.db import migrations


def backfill_muster_required(apps, schema_editor):
    Game = apps.get_model("game", "Game")
    Game.objects.filter(private=False, sandbox=False).update(muster_required=True)


def unbackfill_muster_required(apps, schema_editor):
    Game = apps.get_model("game", "Game")
    Game.objects.filter(private=False, sandbox=False).update(muster_required=False)


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0024_game_muster_deadline_game_muster_job_id_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_muster_required, unbackfill_muster_required),
    ]
