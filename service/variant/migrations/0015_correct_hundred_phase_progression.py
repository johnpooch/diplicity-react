from django.db import migrations


CORRECTED_HUNDRED_PHASE_PROGRESSION = {
    "seasons": ["Year"],
    "transitions": [
        {"from": {"season": "Year", "type": "Movement"},
         "to": {"season": "Year", "type": "Retreat", "yearDelta": 0}},
        {"from": {"season": "Year", "type": "Retreat"},
         "to": {"season": "Year", "type": "Movement", "yearDelta": 5},
         "condition": {"yearMod": 10, "yearModValue": 5}},
        {"from": {"season": "Year", "type": "Retreat"},
         "to": {"season": "Year", "type": "Adjustment", "yearDelta": 0},
         "condition": {"yearMod": 10, "yearModValue": 0}},
        {"from": {"season": "Year", "type": "Adjustment"},
         "to": {"season": "Year", "type": "Movement", "yearDelta": 5}},
    ],
}


PREVIOUS_HUNDRED_PHASE_PROGRESSION = {
    "seasons": ["Year"],
    "transitions": [
        {"from": {"season": "Year", "type": "Movement"},
         "to": {"season": "Year", "type": "Retreat", "yearDelta": 0}},
        {"from": {"season": "Year", "type": "Retreat"},
         "to": {"season": "Year", "type": "Adjustment", "yearDelta": 0}},
        {"from": {"season": "Year", "type": "Adjustment"},
         "to": {"season": "Year", "type": "Movement", "yearDelta": 5}},
    ],
}


def apply_corrected(apps, schema_editor):
    Variant = apps.get_model("variant", "Variant")
    Variant.objects.filter(id="hundred").update(
        phase_progression=CORRECTED_HUNDRED_PHASE_PROGRESSION
    )


def revert_corrected(apps, schema_editor):
    Variant = apps.get_model("variant", "Variant")
    Variant.objects.filter(id="hundred").update(
        phase_progression=PREVIOUS_HUNDRED_PHASE_PROGRESSION
    )


class Migration(migrations.Migration):

    dependencies = [
        ("variant", "0014_backfill_variant_svgs"),
    ]

    operations = [
        migrations.RunPython(apply_corrected, revert_corrected),
    ]
