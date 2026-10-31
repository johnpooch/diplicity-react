from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("member", "0022_commitmententry_departure_kinds"),
    ]

    operations = [
        AddIndexConcurrently(
            model_name="commitmententry",
            index=models.Index(
                fields=["member", "kind"], name="commitment_member_kind_idx"
            ),
        ),
    ]
