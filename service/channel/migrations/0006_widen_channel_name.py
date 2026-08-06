from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("channel", "0005_channelevent"),
    ]

    operations = [
        migrations.AlterField(
            model_name="channel",
            name="name",
            field=models.CharField(max_length=1000),
        ),
    ]
