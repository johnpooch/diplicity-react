#!/bin/bash
set -euo pipefail

echo "Seeding screenshot data..."
SEED_DATA=$(docker exec diplicity-service python3 manage.py seed_screenshot_data)
SEED_FILE=$(mktemp)
echo "$SEED_DATA" > "$SEED_FILE"
trap "rm -f $SEED_FILE" EXIT

echo "Seed data written to $SEED_FILE"
echo "$SEED_DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Game 1: {d[\"game1Id\"]}, Phase 2: {d[\"phase2Id\"]}, Phase 3: {d[\"phase3Id\"]}')"

echo "Running Playwright screenshots..."
cd packages/e2e
SEED_DATA_FILE="$SEED_FILE" npx playwright test --config playwright.screenshots.config.ts

echo ""
echo "Screenshots saved to packages/e2e/screenshots/"
ls -la screenshots/*/
