import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SERVICE_DIR = BASE_DIR.parent / "service"
sys.path.append(str(SERVICE_DIR))

SECRET_KEY = "evals-local-only"
DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

INSTALLED_APPS = [
    "select_orders",
]

DATABASES = {}

USE_TZ = True

EVALS_MODEL = os.getenv("EVALS_MODEL", "anthropic/claude-haiku-4-5")
