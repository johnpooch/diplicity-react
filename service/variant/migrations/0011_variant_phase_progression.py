from django.db import migrations, models

import variant.models


HUNDRED_PHASE_PROGRESSION = {
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


def backfill_hundred_phase_progression(apps, schema_editor):
    Variant = apps.get_model("variant", "Variant")
    Variant.objects.filter(id="hundred").update(phase_progression=HUNDRED_PHASE_PROGRESSION)


class Migration(migrations.Migration):

    dependencies = [
        ("variant", "0010_replace_solo_victory_sc_count_with_victory_conditions"),
    ]

    operations = [
        migrations.AddField(
            model_name="variant",
            name="phase_progression",
            field=models.JSONField(default=variant.models.default_phase_progression),
        ),
        migrations.RunPython(backfill_hundred_phase_progression, migrations.RunPython.noop),
    ]
