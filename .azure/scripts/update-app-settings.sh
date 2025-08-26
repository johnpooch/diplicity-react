#!/bin/bash

# Check if all parameters are provided
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <app> <setting_name> <setting_value>"
    echo "Example: $0 service DATABASE_URL \"@Microsoft.KeyVault(SecretUri=https://diplicityKeyVault.vault.azure.net/secrets/DATABASE-URL)\""
    echo "App must be 'service'"
    exit 1
fi

APP_TYPE="$1"
SETTING_NAME="$2"
SETTING_VALUE="$3"

# Validate app type
if [ "$APP_TYPE" != "service" ]; then
    echo "Error: App must be 'service'"
    exit 1
fi

# Read the app service name from settings.json
APP_SERVICE_NAME=$(grep "\"${APP_TYPE}AppServiceName\"" .azure/settings.json | cut -d'"' -f4)

if [ -z "$APP_SERVICE_NAME" ]; then
    echo "Error: Could not read ${APP_TYPE}AppServiceName from settings.json"
    exit 1
fi

echo "Updating $SETTING_NAME setting for $APP_TYPE App Service: $APP_SERVICE_NAME"

# Update the specified setting
az webapp config appsettings set \
    --name "$APP_SERVICE_NAME" \
    --resource-group "diplicity-react" \
    --settings "$SETTING_NAME=$SETTING_VALUE" 