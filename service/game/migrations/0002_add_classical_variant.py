from django.db import migrations

def add_classical_variant(apps, schema_editor):
    Variant = apps.get_model('game', 'Variant')
    Variant.objects.create(
        name="Classical",
        id="classical",
    )

def remove_classical_variant(apps, schema_editor):
    Variant = apps.get_model('game', 'Variant')
    Variant.objects.filter(id="classical").delete()

class Migration(migrations.Migration):
    dependencies = [
        ('game', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            add_classical_variant,
            remove_classical_variant,
        ),
    ] 