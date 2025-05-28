#!/bin/bash

# Read the serviceAppServiceName from settings.json
APP_SERVICE_NAME=$(grep '"serviceAppServiceName"' .azure/settings.json | cut -d'"' -f4)

if [ -z "$APP_SERVICE_NAME" ]; then
    echo "Error: Could not read serviceAppServiceName from settings.json"
    exit 1
fi

echo "Listing application settings for App Service: $APP_SERVICE_NAME"
echo "----------------------------------------"

# List all application settings
az webapp config appsettings list --name "$APP_SERVICE_NAME" --resource-group "diplicity-react" --query "[].{Name:name, Value:value}" -o table 