from django.db import migrations
from django.db.models import Count


def backfill_member_won(apps, schema_editor):
    Member = apps.get_model("member", "Member")
    Victory = apps.get_model("victory", "Victory")
    solo_victories = Victory.objects.annotate(member_count=Count("members")).filter(
        member_count=1
    )
    Member.objects.filter(victories__in=solo_victories).update(won=True)


class Migration(migrations.Migration):

    dependencies = [
        ("member", "0025_member_left_at"),
        ("victory", "0003_fix_game_and_phase_status_values"),
    ]

    operations = [
        migrations.RunPython(backfill_member_won, migrations.RunPython.noop),
    ]
