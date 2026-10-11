from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("member", "0019_remove_member_departure_booleans_from_state"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE member_member "
                "DROP COLUMN eliminated, "
                "DROP COLUMN kicked, "
                "DROP COLUMN civil_disorder"
            ),
            reverse_sql=(
                "ALTER TABLE member_member "
                "ADD COLUMN eliminated boolean NOT NULL DEFAULT false, "
                "ADD COLUMN kicked boolean NOT NULL DEFAULT false, "
                "ADD COLUMN civil_disorder boolean NOT NULL DEFAULT false"
            ),
        ),
    ]
