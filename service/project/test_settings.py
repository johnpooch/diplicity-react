import os
import subprocess
import sys
from pathlib import Path

SERVICE_DIR = Path(__file__).resolve().parent.parent


def _load_settings(**overrides):
    environment = {
        key: value
        for key, value in os.environ.items()
        if key not in ("DJANGO_SECRET_KEY", "DJANGO_DEBUG")
    }
    environment.update(overrides)
    return subprocess.run(
        [
            sys.executable,
            "-c",
            "import project.settings as settings; print(settings.SECRET_KEY)",
        ],
        cwd=SERVICE_DIR,
        env=environment,
        capture_output=True,
        text=True,
    )


class TestSecretKey:
    def test_settings_refuse_to_load_without_a_secret_key_when_debug_is_off(self):
        result = _load_settings()

        assert result.returncode != 0
        assert (
            "DJANGO_SECRET_KEY must be set when DJANGO_DEBUG is not True."
            in result.stderr
        )

    def test_configured_secret_key_is_used(self):
        result = _load_settings(DJANGO_SECRET_KEY="configured-secret")

        assert result.returncode == 0, result.stderr
        assert result.stdout.splitlines()[-1] == "configured-secret"

    def test_debug_falls_back_to_a_development_key(self):
        result = _load_settings(DJANGO_DEBUG="True")

        assert result.returncode == 0, result.stderr
        assert (
            result.stdout.splitlines()[-1] == "django-insecure-local-development-only"
        )
