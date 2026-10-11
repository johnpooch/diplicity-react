from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("member", "0015_member_withdrawn_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="member",
            name="eliminated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="member",
            name="civil_disorder_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="member",
            name="removed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RenameField(model_name="member", old_name="eliminated", new_name="legacy_eliminated"),
                migrations.AlterField(
                    model_name="member",
                    name="legacy_eliminated",
                    field=models.BooleanField(db_column="eliminated", default=False),
                ),
                migrations.RenameField(model_name="member", old_name="kicked", new_name="legacy_kicked"),
                migrations.AlterField(
                    model_name="member",
                    name="legacy_kicked",
                    field=models.BooleanField(db_column="kicked", default=False),
                ),
                migrations.RenameField(model_name="member", old_name="civil_disorder", new_name="legacy_civil_disorder"),
                migrations.AlterField(
                    model_name="member",
                    name="legacy_civil_disorder",
                    field=models.BooleanField(db_column="civil_disorder", default=False),
                ),
            ],
        ),
    ]
