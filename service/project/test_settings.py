import os
import subprocess
import sys
from pathlib import Path

SERVICE_DIR = Path(__file__).resolve().parent.parent


def _load_setting(name, **overrides):
    environment = {
        key: value
        for key, value in os.environ.items()
        if key not in ("DJANGO_CORS_ALLOWED_ORIGIN_REGEXES", "GIT_SHA")
    }
    environment.update(DJANGO_SECRET_KEY="test-secret", **overrides)
    return subprocess.run(
        [
            sys.executable,
            "-c",
            f"import project.settings as settings; print(repr(settings.{name}))",
        ],
        cwd=SERVICE_DIR,
        env=environment,
        capture_output=True,
        text=True,
    )


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


class TestCorsAllowedOriginRegexes:
    def test_defaults_to_an_empty_list(self):
        result = _load_setting("CORS_ALLOWED_ORIGIN_REGEXES")

        assert result.returncode == 0, result.stderr
        assert result.stdout.splitlines()[-1] == "[]"

    def test_empty_variable_yields_an_empty_list(self):
        result = _load_setting(
            "CORS_ALLOWED_ORIGIN_REGEXES", DJANGO_CORS_ALLOWED_ORIGIN_REGEXES=""
        )

        assert result.returncode == 0, result.stderr
        assert result.stdout.splitlines()[-1] == "[]"

    def test_variable_is_split_on_commas(self):
        result = _load_setting(
            "CORS_ALLOWED_ORIGIN_REGEXES",
            DJANGO_CORS_ALLOWED_ORIGIN_REGEXES=r"^https://deploy-preview-\d+--diplicity-react\.netlify\.app$,^https://other\.example\.com$",
        )

        assert result.returncode == 0, result.stderr
        assert result.stdout.splitlines()[-1] == (
            "['^https://deploy-preview-\\\\d+--diplicity-react\\\\.netlify\\\\.app$', "
            "'^https://other\\\\.example\\\\.com$']"
        )


class TestVersion:
    def test_defaults_when_git_sha_is_unset(self):
        result = _load_setting("VERSION")

        assert result.stdout.splitlines()[-1] == "'0.0.0'"

    def test_defaults_when_git_sha_is_empty(self):
        result = _load_setting("VERSION", GIT_SHA="")

        assert result.stdout.splitlines()[-1] == "'0.0.0'"

    def test_uses_git_sha(self):
        result = _load_setting("VERSION", GIT_SHA="abc123")

        assert result.stdout.splitlines()[-1] == "'abc123'"
