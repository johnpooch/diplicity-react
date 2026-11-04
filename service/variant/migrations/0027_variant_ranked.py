from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("variant", "0026_resanitize_variant_svgs"),
    ]

    operations = [
        migrations.AddField(
            model_name="variant",
            name="ranked",
            field=models.BooleanField(db_default=False, default=False),
        ),
    ]
