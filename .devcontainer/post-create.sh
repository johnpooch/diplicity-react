#!/usr/bin/env bash
set -euo pipefail

cd /workspaces/diplicity-react

export HOME="${HOME:-/tmp/inspect-ai-home}"
export XDG_DATA_HOME="${XDG_DATA_HOME:-/tmp/inspect-ai-data}"

if ! mkdir -p "$HOME" "$XDG_DATA_HOME" 2>/dev/null; then
  export HOME="/tmp/inspect-ai-home"
  export XDG_DATA_HOME="/tmp/inspect-ai-data"
  mkdir -p "$HOME" "$XDG_DATA_HOME"
fi

for shell_rc in "$HOME/.bash_profile" "$HOME/.bashrc" "$HOME/.profile"; do
  mkdir -p "$(dirname "$shell_rc")"
  if [ -f "$shell_rc" ]; then
    if ! grep -Fqx 'export HOME="/tmp/inspect-ai-home"' "$shell_rc"; then
      printf '\n# devcontainer inspect-ai home fallback\nexport HOME="/tmp/inspect-ai-home"\nexport XDG_DATA_HOME="/tmp/inspect-ai-data"\n' >> "$shell_rc"
    fi
  else
    printf '# devcontainer inspect-ai home fallback\nexport HOME="/tmp/inspect-ai-home"\nexport XDG_DATA_HOME="/tmp/inspect-ai-data"\n' > "$shell_rc"
  fi
done

VENV_DIR=".venv"
VENV_PYTHON="$VENV_DIR/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
  rm -rf "$VENV_DIR"
  python3.12 -m venv "$VENV_DIR"
elif ! "$VENV_PYTHON" -c 'import sys; print(sys.executable)' >/dev/null 2>&1; then
  rm -rf "$VENV_DIR"
  python3.12 -m venv "$VENV_DIR"
fi

. "$VENV_DIR/bin/activate"

export PIP_DISABLE_PIP_VERSION_CHECK=1
export PIP_NO_CACHE_DIR=1

python -m pip install --upgrade pip setuptools wheel
python -m pip install -r service/requirements.txt -r service/dev_requirements.txt

for attempt in $(seq 1 20); do
  if python - <<'PY'
import sys
import psycopg

try:
    with psycopg.connect("dbname=diplicity user=postgres password=postgres host=db port=5432") as conn:
        conn.execute("SELECT 1")
except Exception:
    sys.exit(1)
PY
  then
    break
  fi

  if [ "$attempt" -eq 20 ]; then
    echo "Database did not become ready in time; skipping migrations."
    exit 0
  fi

  sleep 2
done

cd service
python manage.py migrate --noinput
python manage.py check
