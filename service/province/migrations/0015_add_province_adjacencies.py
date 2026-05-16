from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('province', '0014_province_home_nation'),
    ]

    operations = [
        migrations.AddField(
            model_name='province',
            name='adjacencies',
            field=models.JSONField(default=list),
        ),
    ]
