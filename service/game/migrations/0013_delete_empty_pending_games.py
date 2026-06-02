from django.db import migrations
from django.db.models import Count


def delete_empty_pending_games(apps, schema_editor):
    Game = apps.get_model("game", "Game")
    Game.objects.filter(status="pending").annotate(
        member_count=Count("members")
    ).filter(member_count=0).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0012_add_press_type_field"),
    ]

    operations = [
        migrations.RunPython(
            delete_empty_pending_games,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
