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
