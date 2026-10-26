from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, connections


class Command(BaseCommand):
    help = "Drops and recreates the public schema of the staging database"

    def add_arguments(self, parser):
        parser.add_argument("--database", type=str, default=DEFAULT_DB_ALIAS)

    def handle(self, *args, **options):
        if settings.ENVIRONMENT != "staging":
            raise CommandError("reset_staging only runs with ENVIRONMENT=staging")

        with connections[options["database"]].cursor() as cursor:
            cursor.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = current_database() AND pid <> pg_backend_pid()"
            )
            cursor.execute("DROP SCHEMA public CASCADE")
            cursor.execute("CREATE SCHEMA public")

        self.stdout.write(self.style.SUCCESS("Reset the staging database."))
