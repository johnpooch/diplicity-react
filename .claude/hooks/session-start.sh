#!/bin/bash
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

if [ -z "${RAILWAY_ACCOUNT_TOKEN:-}" ]; then
  echo "RAILWAY_ACCOUNT_TOKEN not set — Railway CLI will not be authenticated in this session." >&2
  exit 0
fi

mkdir -p ~/.railway
printf '{"token":"%s"}' "${RAILWAY_ACCOUNT_TOKEN}" > ~/.railway/config.json
echo "Railway CLI authenticated."
