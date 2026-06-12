#!/bin/bash
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

if [ -z "${RAILWAY_API_TOKEN:-}" ]; then
  echo "RAILWAY_API_TOKEN not set — Railway CLI will not be authenticated in this session." >&2
  exit 0
fi

railway link --environment production --service diplicity-react 39039c2c-4f5d-4a37-8c0d-f8e4279fce61
echo "Railway CLI authenticated and project linked."
