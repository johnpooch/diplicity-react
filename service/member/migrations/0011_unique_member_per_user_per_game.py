from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("member", "0010_backfill_member_sandbox"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="member",
            constraint=models.UniqueConstraint(
                condition=models.Q(("sandbox", False)),
                fields=("game", "user"),
                name="unique_member_per_user_per_game",
            ),
        ),
    ]
