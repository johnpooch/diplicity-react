from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("nation", "0013_remove_non_playable"),
    ]

    operations = [
        migrations.AddField(
            model_name="nation",
            name="non_playable",
            field=models.BooleanField(default=False),
        ),
    ]
