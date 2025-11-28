from django.db import migrations


def revert_spring_to_year_for_hundred(apps, schema_editor):
    Phase = apps.get_model("phase", "Phase")
    Variant = apps.get_model("variant", "Variant")

    try:
        hundred_variant = Variant.objects.get(id="hundred")
        Phase.objects.filter(variant=hundred_variant).update(season="Year")
    except Variant.DoesNotExist:
        pass


def revert_year_to_spring_for_hundred(apps, schema_editor):
    Phase = apps.get_model("phase", "Phase")
    Variant = apps.get_model("variant", "Variant")

    try:
        hundred_variant = Variant.objects.get(id="hundred")
        Phase.objects.filter(variant=hundred_variant, season="Year").update(season="Spring")
    except Variant.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ("phase", "0008_fix_year_season_to_spring"),
    ]

    operations = [
        migrations.RunPython(
            revert_spring_to_year_for_hundred,
            revert_year_to_spring_for_hundred,
        ),
    ]
