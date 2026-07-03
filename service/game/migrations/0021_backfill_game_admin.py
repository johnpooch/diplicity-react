from django.db import migrations
from django.db.models import F


def backfill_game_admin(apps, schema_editor):
    Game = apps.get_model("game", "Game")
    Game.objects.filter(game_master__isnull=False).update(admin=F("game_master"))
    Game.objects.filter(game_master__isnull=True).update(admin=F("created_by"))


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0020_game_admin"),
    ]

    operations = [
        migrations.RunPython(backfill_game_admin, migrations.RunPython.noop),
    ]
