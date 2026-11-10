# pytest configuration
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.infrastructure.config.settings")

# Integration tests run against an in-memory SQLite database so the suite
# works without a live PostgreSQL instance; production keeps PostgreSQL.
os.environ.setdefault("DATABASE_ENGINE", "django.db.backends.sqlite3")

pytest_plugins = ["pytest_django"]
