from django.db import connection


class TestDatabaseDriver:
    def test_django_uses_psycopg_with_the_compiled_implementation(self):
        assert connection.Database.__name__ == "psycopg"
        assert connection.Database.pq.__impl__ in ("binary", "c")
