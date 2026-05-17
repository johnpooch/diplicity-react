from django.db import migrations, models

import variant.models


def backfill_victory_conditions(apps, schema_editor):
    Variant = apps.get_model("variant", "Variant")
    variants = list(Variant.objects.all())
    for variant in variants:
        variant.victory_conditions = {
            "soloVictorySupplyCenters": variant.solo_victory_sc_count,
            "gameEndsYear": None,
            "drawAfterYear": None,
        }
    Variant.objects.bulk_update(variants, ["victory_conditions"])


def reverse_victory_conditions(apps, schema_editor):
    Variant = apps.get_model("variant", "Variant")
    variants = list(Variant.objects.all())
    for variant in variants:
        variant.solo_victory_sc_count = variant.victory_conditions["soloVictorySupplyCenters"]
    Variant.objects.bulk_update(variants, ["solo_victory_sc_count"])


class Migration(migrations.Migration):

    dependencies = [
        ("variant", "0009_variant_adjudication_modifiers"),
    ]

    operations = [
        migrations.AddField(
            model_name="variant",
            name="victory_conditions",
            field=models.JSONField(default=variant.models.default_victory_conditions),
        ),
        migrations.RunPython(backfill_victory_conditions, reverse_victory_conditions),
        migrations.RemoveField(
            model_name="variant",
            name="solo_victory_sc_count",
        ),
    ]
