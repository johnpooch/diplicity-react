#!/bin/bash

# Check if both parameters are provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <setting_name> <setting_value>"
    echo "Example: $0 VITE_GOOGLE_CLIENT_ID \"your-client-id\""
    exit 1
fi

SETTING_NAME="$1"
SETTING_VALUE="$2"

# Read the static web app name from settings.json
STATIC_WEB_APP_NAME=$(grep '"staticWebAppName"' .azure/settings.json | cut -d'"' -f4)

if [ -z "$STATIC_WEB_APP_NAME" ]; then
    echo "Error: Could not read staticWebAppName from settings.json"
    exit 1
fi

echo "Updating $SETTING_NAME setting for Static Web App: $STATIC_WEB_APP_NAME"

# Update the specified setting
az staticwebapp appsettings set \
    --name "$STATIC_WEB_APP_NAME" \
    --setting-names "$SETTING_NAME=$SETTING_VALUE" 