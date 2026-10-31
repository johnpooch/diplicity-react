from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("member", "0018_rebackfill_member_departure_timestamps"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE member_member "
                        "ALTER COLUMN eliminated SET DEFAULT false, "
                        "ALTER COLUMN kicked SET DEFAULT false, "
                        "ALTER COLUMN civil_disorder SET DEFAULT false"
                    ),
                    reverse_sql=(
                        "ALTER TABLE member_member "
                        "ALTER COLUMN eliminated DROP DEFAULT, "
                        "ALTER COLUMN kicked DROP DEFAULT, "
                        "ALTER COLUMN civil_disorder DROP DEFAULT"
                    ),
                ),
            ],
            state_operations=[
                migrations.RemoveField(model_name="member", name="legacy_eliminated"),
                migrations.RemoveField(model_name="member", name="legacy_kicked"),
                migrations.RemoveField(
                    model_name="member", name="legacy_civil_disorder"
                ),
            ],
        ),
    ]
