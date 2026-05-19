# Converts Variant.victory_conditions from the legacy flat object
# ({soloVictorySupplyCenters, gameEndsYear, drawAfterYear}) into the canonical
# variant.schema.yaml shape: a list of discriminated VictoryCondition objects.

from django.db import migrations


def convert_to_list(apps, schema_editor):
    Variant = apps.get_model("variant", "Variant")
    variants = list(Variant.objects.all())
    for variant in variants:
        legacy = variant.victory_conditions
        if isinstance(legacy, list):
            continue
        conditions = [
            {
                "type": "supply-center-majority",
                "supplyCenters": legacy["soloVictorySupplyCenters"],
            }
        ]
        if legacy.get("gameEndsYear") is not None:
            conditions.append(
                {
                    "type": "timed-resolution",
                    "year": legacy["gameEndsYear"],
                    "resolution": "most-supply-centers",
                }
            )
        if legacy.get("drawAfterYear") is not None:
            conditions.append(
                {
                    "type": "timed-resolution",
                    "year": legacy["drawAfterYear"],
                    "resolution": "shared-draw",
                }
            )
        variant.victory_conditions = conditions
    Variant.objects.bulk_update(variants, ["victory_conditions"])


def convert_to_object(apps, schema_editor):
    Variant = apps.get_model("variant", "Variant")
    variants = list(Variant.objects.all())
    for variant in variants:
        canonical = variant.victory_conditions
        if isinstance(canonical, dict):
            continue
        legacy = {
            "soloVictorySupplyCenters": None,
            "gameEndsYear": None,
            "drawAfterYear": None,
        }
        for condition in canonical:
            if condition["type"] == "supply-center-majority":
                legacy["soloVictorySupplyCenters"] = condition["supplyCenters"]
            elif condition["type"] == "timed-resolution":
                if condition["resolution"] == "shared-draw":
                    legacy["drawAfterYear"] = condition["year"]
                else:
                    legacy["gameEndsYear"] = condition["year"]
        variant.victory_conditions = legacy
    Variant.objects.bulk_update(variants, ["victory_conditions"])


class Migration(migrations.Migration):

    dependencies = [
        ("variant", "0012_variant_rules"),
    ]

    operations = [
        migrations.RunPython(convert_to_list, convert_to_object),
    ]
