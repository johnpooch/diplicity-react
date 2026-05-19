from django.db import migrations


BUILD_ANYWHERE_MODIFIER = "allow-builds-in-non-home-centers"


def add_modifier(apps, schema_editor):
    Variant = apps.get_model("variant", "Variant")
    Variant.objects.filter(id="hundred").update(
        adjudication_modifiers=[BUILD_ANYWHERE_MODIFIER]
    )


def remove_modifier(apps, schema_editor):
    Variant = apps.get_model("variant", "Variant")
    Variant.objects.filter(id="hundred").update(adjudication_modifiers=[])


class Migration(migrations.Migration):

    dependencies = [
        ("variant", "0016_merge_20260517_2236"),
    ]

    operations = [
        migrations.RunPython(add_modifier, remove_modifier),
    ]
