from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('member', '0004_make_user_nullable'),
    ]

    operations = [
        migrations.AddField(
            model_name='member',
            name='civil_disorder',
            field=models.BooleanField(default=False),
        ),
    ]
