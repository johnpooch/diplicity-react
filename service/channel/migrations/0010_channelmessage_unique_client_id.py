from django.db import migrations, models


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("channel", "0009_channelmessage_client_message_id"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS channel_message_unique_client_id_per_sender "
                        "ON channel_channelmessage (sender_id, client_message_id) "
                        "WHERE client_message_id IS NOT NULL"
                    ),
                    reverse_sql="DROP INDEX CONCURRENTLY IF EXISTS channel_message_unique_client_id_per_sender",
                ),
            ],
            state_operations=[
                migrations.AddConstraint(
                    model_name="channelmessage",
                    constraint=models.UniqueConstraint(
                        condition=models.Q(("client_message_id__isnull", False)),
                        fields=("sender", "client_message_id"),
                        name="channel_message_unique_client_id_per_sender",
                    ),
                ),
            ],
        ),
    ]
