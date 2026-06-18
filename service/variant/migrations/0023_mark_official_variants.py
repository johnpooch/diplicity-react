from django.db import migrations


OFFICIAL_IDS = ["classical", "vietnam-war", "italy-vs-germany", "hundred"]


def mark_official(apps, schema_editor):
    Variant = apps.get_model("variant", "Variant")
    Variant.objects.filter(id__in=OFFICIAL_IDS).update(official=True)


def unmark_official(apps, schema_editor):
    Variant = apps.get_model("variant", "Variant")
    Variant.objects.filter(id__in=OFFICIAL_IDS).update(official=False)


class Migration(migrations.Migration):

    dependencies = [
        ("variant", "0022_variant_official"),
    ]

    operations = [
        migrations.RunPython(mark_official, unmark_official),
    ]
