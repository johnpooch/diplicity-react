from django.db import migrations
from django.utils import timezone


def rank(apps, schema_editor):
    Variant = apps.get_model("variant", "Variant")
    Nation = apps.get_model("nation", "Nation")

    playable = Nation.objects.filter(non_playable=False)
    handicapped = playable.values("variant_id").distinct()
    unhandicapped = playable.filter(handicap__isnull=True).values("variant_id")
    Variant.objects.filter(id__in=handicapped).exclude(id__in=unhandicapped).update(
        ranked=True, updated_at=timezone.now()
    )


def unrank(apps, schema_editor):
    Variant = apps.get_model("variant", "Variant")
    Variant.objects.filter(ranked=True).update(ranked=False, updated_at=timezone.now())


class Migration(migrations.Migration):

    dependencies = [
        ("variant", "0027_variant_ranked"),
        ("rating", "0002_seed_nation_handicaps"),
    ]

    operations = [
        migrations.RunPython(rank, unrank),
    ]
