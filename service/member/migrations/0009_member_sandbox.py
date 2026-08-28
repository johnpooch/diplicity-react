from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("member", "0008_nationpreference_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="member",
            name="sandbox",
            field=models.BooleanField(default=False),
        ),
    ]
