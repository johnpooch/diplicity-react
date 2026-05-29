from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('variant', '0020_add_status_and_owner'),
    ]
    operations = [
        migrations.AddField(
            model_name='variant',
            name='dominance_rules',
            field=models.JSONField(default=list),
        ),
    ]
