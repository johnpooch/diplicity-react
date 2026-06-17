from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("variant", "0021_add_dominance_rules"),
    ]

    operations = [
        migrations.AlterField(
            model_name="variant",
            name="id",
            field=models.CharField(max_length=64, primary_key=True, serialize=False),
        ),
    ]
