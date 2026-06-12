from django.db import migrations


def backfill_created_by(apps, schema_editor):
    Member = apps.get_model("member", "Member")
    Game = apps.get_model("game", "Game")
    gm_members = Member.objects.filter(is_game_master=True, user__isnull=False)
    games = []
    for member in gm_members.iterator():
        games.append(Game(id=member.game_id, created_by_id=member.user_id))
    Game.objects.bulk_update(games, ["created_by"], batch_size=500)


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0016_game_created_by"),
        ("member", "0005_member_civil_disorder"),
    ]

    operations = [
        migrations.RunPython(backfill_created_by, migrations.RunPython.noop),
    ]
