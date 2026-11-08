from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("member", "0025_member_left_at"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE member_member "
                        "ALTER COLUMN won SET DEFAULT false, "
                        "ALTER COLUMN drew SET DEFAULT false"
                    ),
                    reverse_sql=(
                        "ALTER TABLE member_member "
                        "ALTER COLUMN won DROP DEFAULT, "
                        "ALTER COLUMN drew DROP DEFAULT"
                    ),
                ),
            ],
            state_operations=[
                migrations.RemoveField(model_name="member", name="won"),
                migrations.RemoveField(model_name="member", name="drew"),
            ],
        ),
    ]
