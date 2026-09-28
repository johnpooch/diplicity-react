import ast

from django.conf import settings

ALLOWED_SERVICE_PACKAGES = {"adjudicator", "dumbbot"}
IGNORED_DIRECTORIES = {".venv", "node_modules"}


def _packages(root):
    return {path.name for path in root.iterdir() if (path / "__init__.py").exists()}


def _evals_sources():
    for path in settings.BASE_DIR.rglob("*.py"):
        if not IGNORED_DIRECTORIES.intersection(path.relative_to(settings.BASE_DIR).parts):
            yield path


def _imported_roots(path):
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            yield node.module.split(".")[0]


class TestServiceBoundary:

    def test_evals_imports_only_allowed_service_packages(self):
        forbidden = _packages(settings.SERVICE_DIR) - ALLOWED_SERVICE_PACKAGES
        violations = sorted(
            f"{path.relative_to(settings.BASE_DIR)}: {root}"
            for path in _evals_sources()
            for root in _imported_roots(path)
            if root in forbidden
        )
        assert violations == []

    def test_evals_packages_do_not_shadow_service_packages(self):
        assert _packages(settings.BASE_DIR) & _packages(settings.SERVICE_DIR) == set()
