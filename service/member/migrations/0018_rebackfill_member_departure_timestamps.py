from django.db import migrations
from django.db.models import F, Q


def backfill_departure_timestamps(apps, schema_editor):
    Member = apps.get_model("member", "Member")

    Member.objects.filter(legacy_eliminated=True, eliminated_at__isnull=True).update(
        eliminated_at=F("updated_at")
    )
    Member.objects.filter(
        legacy_civil_disorder=True, civil_disorder_at__isnull=True
    ).update(civil_disorder_at=F("updated_at"))
    Member.objects.filter(legacy_kicked=True, removed_at__isnull=True).exclude(
        Q(legacy_civil_disorder=True) | Q(withdrawn_at__isnull=False),
        replaced_by__isnull=False,
    ).update(removed_at=F("updated_at"))


class Migration(migrations.Migration):

    dependencies = [
        ("member", "0017_backfill_member_departure_timestamps"),
    ]

    operations = [
        migrations.RunPython(backfill_departure_timestamps, migrations.RunPython.noop),
    ]
