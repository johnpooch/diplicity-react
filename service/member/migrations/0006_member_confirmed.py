from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('member', '0005_member_civil_disorder'),
    ]

    operations = [
        migrations.AddField(
            model_name='member',
            name='confirmed',
            field=models.BooleanField(default=False),
        ),
    ]
