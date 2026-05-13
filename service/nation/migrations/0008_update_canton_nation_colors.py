from django.db import migrations

UPDATED_COLORS = {
    'Britain': '#2198F5',
    'China': '#F33F35',
    'Holland': '#F56B26',
    'Japan': '#4CAF50',
}


def update_canton_nation_colors(apps, schema_editor):
    Variant = apps.get_model("variant", "Variant")
    Nation = apps.get_model("nation", "Nation")

    canton_variant = Variant.objects.get(id="canton")
    for name, color in UPDATED_COLORS.items():
        Nation.objects.filter(variant=canton_variant, name=name).update(color=color)


def revert_canton_nation_colors(apps, schema_editor):
    Variant = apps.get_model("variant", "Variant")
    Nation = apps.get_model("nation", "Nation")

    canton_variant = Variant.objects.get(id="canton")
    for name in UPDATED_COLORS:
        Nation.objects.filter(variant=canton_variant, name=name).update(color='#808080')


class Migration(migrations.Migration):

    dependencies = [
        ("nation", "0007_add_canton_nations"),
        ("variant", "0008_add_canton_variant"),
    ]

    operations = [
        migrations.RunPython(
            update_canton_nation_colors,
            revert_canton_nation_colors,
        ),
    ]
