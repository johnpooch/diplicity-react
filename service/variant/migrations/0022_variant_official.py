from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("variant", "0021_add_dominance_rules"),
    ]

    operations = [
        migrations.AddField(
            model_name="variant",
            name="official",
            field=models.BooleanField(default=False),
        ),
    ]
