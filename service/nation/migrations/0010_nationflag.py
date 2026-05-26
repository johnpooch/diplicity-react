from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("nation", "0009_add_nation_id"),
    ]

    operations = [
        migrations.CreateModel(
            name="NationFlag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("svg", models.TextField()),
                ("content_hash", models.CharField(editable=False, max_length=64)),
                (
                    "nation",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="flag",
                        to="nation.nation",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
