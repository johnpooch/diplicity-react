from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0005_alter_orderresolution_status'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='order',
                    name='is_implicit',
                    field=models.BooleanField(default=False),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql='ALTER TABLE "order_order" ADD COLUMN IF NOT EXISTS "is_implicit" boolean NOT NULL DEFAULT false;',
                    reverse_sql='ALTER TABLE "order_order" DROP COLUMN IF EXISTS "is_implicit";',
                ),
            ],
        ),
    ]
