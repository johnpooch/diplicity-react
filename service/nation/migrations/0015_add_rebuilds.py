from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("nation", "0014_add_non_playable"),
    ]

    operations = [
        migrations.AddField(
            model_name="nation",
            name="rebuilds",
            field=models.BooleanField(default=False),
        ),
    ]
