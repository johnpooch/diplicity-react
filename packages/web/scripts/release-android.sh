#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEB_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ ! -f "$WEB_DIR/.env.release" ]; then
  echo "Missing $WEB_DIR/.env.release — copy .env.release.example and fill in credentials"
  exit 1
fi

set -a
# shellcheck source=/dev/null
source "$WEB_DIR/.env.release"
set +a

cd "$WEB_DIR"
npm run build
ANDROID_HOME="$HOME/Android/Sdk" npx cap sync android
bundle exec fastlane android release
