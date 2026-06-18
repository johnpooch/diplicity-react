from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("variant", "0023_mark_official_variants"),
    ]

    operations = [
        migrations.AlterField(
            model_name="variant",
            name="id",
            field=models.CharField(max_length=64, primary_key=True, serialize=False),
        ),
    ]
