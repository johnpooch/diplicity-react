from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("nation", "0012_add_non_playable"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="nation",
            name="non_playable",
        ),
    ]
