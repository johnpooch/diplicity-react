from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user_profile", "0006_userprofile_commitment"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="kind",
            field=models.CharField(
                choices=[("human", "Human"), ("llm", "LLM"), ("dumbbot", "DumbBot")],
                default="human",
                max_length=20,
            ),
        ),
    ]
