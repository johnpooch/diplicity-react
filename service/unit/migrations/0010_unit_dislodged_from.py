from django.db import migrations, models
import django.db.models.deletion


def populate_dislodged_from(apps, schema_editor):
    Unit = apps.get_model("unit", "Unit")
    units = list(Unit.objects.filter(dislodged_by__isnull=False).select_related("dislodged_by"))
    for unit in units:
        unit.dislodged_from_id = unit.dislodged_by.province_id
    Unit.objects.bulk_update(units, ["dislodged_from"])


class Migration(migrations.Migration):

    dependencies = [
        ("province", "0001_initial"),
        ("unit", "0009_add_canton_units"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="unit",
            name="dislodged_by_requires_dislodged",
        ),
        migrations.AddField(
            model_name="unit",
            name="dislodged_from",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="units_dislodged_from",
                to="province.province",
            ),
        ),
        migrations.RunPython(populate_dislodged_from, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="unit",
            name="dislodged_by",
        ),
        migrations.AddConstraint(
            model_name="unit",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("dislodged", False), ("dislodged_from__isnull", True)),
                    ("dislodged", True),
                    _connector="OR",
                ),
                name="dislodged_from_requires_dislodged",
            ),
        ),
    ]
