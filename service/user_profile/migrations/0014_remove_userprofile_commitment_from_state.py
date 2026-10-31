from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("user_profile", "0013_userprofile_is_moderator"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE user_profile_userprofile "
                        "ALTER COLUMN commitment SET DEFAULT 'undefined'"
                    ),
                    reverse_sql=(
                        "ALTER TABLE user_profile_userprofile "
                        "ALTER COLUMN commitment DROP DEFAULT"
                    ),
                ),
            ],
            state_operations=[
                migrations.RemoveField(model_name="userprofile", name="commitment"),
            ],
        ),
    ]
