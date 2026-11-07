from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="RailwayMetricsCursor",
            fields=[
                (
                    "environment_id",
                    models.CharField(max_length=36, primary_key=True, serialize=False),
                ),
                ("exported_until", models.DateTimeField()),
            ],
        ),
    ]
