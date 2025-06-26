from django.core.management.base import BaseCommand
from django.apps import apps


class Command(BaseCommand):
    help = "Clear all data from the database"

    def handle(self, *args, **kwargs):
        self.stdout.write("Clearing all data from the database...")

        for model in apps.get_models():
            model_name = model.__name__
            try:
                count, _ = model.objects.all().delete()
                self.stdout.write(f"Deleted {count} records from {model_name}.")
            except Exception as e:
                self.stderr.write(f"Failed to delete data from {model_name}: {e}")

        self.stdout.write("Database cleared successfully.")
