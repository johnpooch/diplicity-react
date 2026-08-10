from django.db import migrations


def backfill_member_sandbox(apps, schema_editor):
    Member = apps.get_model("member", "Member")
    Member.objects.filter(game__sandbox=True).update(sandbox=True)


class Migration(migrations.Migration):

    dependencies = [
        ("member", "0008_member_sandbox"),
        ("game", "0004_game_sandbox_alter_game_movement_phase_duration"),
    ]

    operations = [
        migrations.RunPython(backfill_member_sandbox, migrations.RunPython.noop),
    ]
