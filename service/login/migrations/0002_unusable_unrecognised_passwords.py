from django.contrib.auth.hashers import (
    UNUSABLE_PASSWORD_PREFIX,
    identify_hasher,
    make_password,
)
from django.db import migrations


def _is_recognised_hash(password):
    try:
        identify_hasher(password)
    except ValueError:
        return False
    return True


def make_unrecognised_passwords_unusable(apps, schema_editor):
    User = apps.get_model("auth", "User")

    scanned = User.objects.exclude(
        password__startswith=UNUSABLE_PASSWORD_PREFIX
    ).values_list("id", "password")
    for user_id, password in scanned.iterator():
        if not _is_recognised_hash(password):
            User.objects.filter(id=user_id, password=password).update(
                password=make_password(None)
            )


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
