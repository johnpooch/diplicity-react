from django.db import migrations


def update_colors(apps, schema_editor):
    Nation = apps.get_model("nation", "Nation")
    Variant = apps.get_model("variant", "Variant")

    variant = Variant.objects.get(id="youngstown-redux")
    color_map = {
        "Britain": "#2196F3",
        "China": "#9C27B0",
        "Japan": "#FFD700",
        "Germany": "#795548",
        "India": "#FF9800",
    }
    for name, color in color_map.items():
        Nation.objects.filter(variant=variant, name=name).update(color=color)


def revert_colors(apps, schema_editor):
    Nation = apps.get_model("nation", "Nation")
    Variant = apps.get_model("variant", "Variant")

    variant = Variant.objects.get(id="youngstown-redux")
    for name in ["Britain", "China", "Japan", "India"]:
        Nation.objects.filter(variant=variant, name=name).update(color="#808080")
    Nation.objects.filter(variant=variant, name="Germany").update(color="#90A4AE")


class Migration(migrations.Migration):

    dependencies = [
        ("nation", "0005_add_youngstown_redux_nations"),
    ]

    operations = [
        migrations.RunPython(update_colors, revert_colors),
    ]
