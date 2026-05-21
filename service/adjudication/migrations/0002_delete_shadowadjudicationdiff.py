from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("adjudication", "0001_initial"),
    ]

    operations = [
        migrations.DeleteModel(
            name="ShadowAdjudicationDiff",
        ),
    ]
