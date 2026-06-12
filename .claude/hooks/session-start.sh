#!/bin/bash
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

if [ -z "${RAILWAY_API_TOKEN:-}" ]; then
  echo "RAILWAY_API_TOKEN not set — Railway CLI will not be authenticated in this session." >&2
  exit 0
fi

echo "Railway CLI authenticated."

if [ -z "${RAILWAY_TOKEN:-}" ]; then
  echo "RAILWAY_TOKEN not set — 'railway run' (prod-query) will not be available in this session." >&2
else
  echo "Installing service Python dependencies for railway run..."
  pip install -q -r /home/user/diplicity-react/service/requirements.txt && \
    echo "Service dependencies installed." || \
    echo "Warning: failed to install service dependencies — prod-query may not work." >&2
fi
