from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX, identify_hasher, make_password
from django.db import migrations


def _is_recognised_hash(password):
    try:
        identify_hasher(password)
    except ValueError:
        return False
    return True


def make_unrecognised_passwords_unusable(apps, schema_editor):
    User = apps.get_model("auth", "User")

    users = []
    for user in User.objects.exclude(password__startswith=UNUSABLE_PASSWORD_PREFIX).only("id", "password").iterator():
        if not _is_recognised_hash(user.password):
            user.password = make_password(None)
            users.append(user)

    User.objects.bulk_update(users, ["password"], batch_size=500)


class Migration(migrations.Migration):

    dependencies = [
        ("login", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            make_unrecognised_passwords_unusable,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
