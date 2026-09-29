from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("variant", "0024_widen_variant_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="variant",
            name="horizontal_wrap",
            field=models.BooleanField(default=False),
        ),
    ]
