from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('member', '0007_member_seeking_replacement_replaced_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='member',
            name='confirmed',
            field=models.BooleanField(default=False),
        ),
    ]
