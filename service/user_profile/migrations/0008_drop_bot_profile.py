from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("user_profile", "0007_userprofile_kind"),
    ]

    operations = [
        migrations.RunSQL(
            "DROP TABLE IF EXISTS bot_profile_botprofile",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
