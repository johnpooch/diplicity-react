from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('province', '0013_add_canton_provinces'),
    ]

    operations = [
        migrations.AddField(
            model_name='province',
            name='adjacencies',
            field=models.JSONField(default=list),
        ),
    ]
