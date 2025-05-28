#!/bin/bash

# Read the static web app name from settings.json
STATIC_WEB_APP_NAME=$(grep '"staticWebAppName"' .azure/settings.json | cut -d'"' -f4)

if [ -z "$STATIC_WEB_APP_NAME" ]; then
    echo "Error: Could not read staticWebAppName from settings.json"
    exit 1
fi

echo "Listing settings for Static Web App: $STATIC_WEB_APP_NAME"
echo "----------------------------------------"

# List all settings
az staticwebapp appsettings list \
    --name "$STATIC_WEB_APP_NAME" \
    --query "[].{Name:name, Value:value}" \
    -o table 