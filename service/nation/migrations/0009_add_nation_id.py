from django.db import migrations, models
from django.utils.text import slugify


def backfill_nation_id(apps, schema_editor):
    Nation = apps.get_model("nation", "Nation")
    nations = list(Nation.objects.all())
    for nation in nations:
        nation.nation_id = slugify(nation.name)
    Nation.objects.bulk_update(nations, ["nation_id"])


def clear_nation_id(apps, schema_editor):
    Nation = apps.get_model("nation", "Nation")
    Nation.objects.update(nation_id="")


class Migration(migrations.Migration):

    dependencies = [
        ("nation", "0008_update_canton_nation_colors"),
    ]

    operations = [
        migrations.AddField(
            model_name="nation",
            name="nation_id",
            field=models.CharField(default="", max_length=50),
            preserve_default=False,
        ),
        migrations.RunPython(
            backfill_nation_id,
            clear_nation_id,
        ),
        migrations.AlterUniqueTogether(
            name="nation",
            unique_together={("name", "variant"), ("nation_id", "variant")},
        ),
    ]
