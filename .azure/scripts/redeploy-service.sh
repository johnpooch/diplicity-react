
#!/bin/bash

# Variables
WEB_APP_NAME="diplicity-service"
RESOURCE_GROUP="diplicity-react"
DOCKER_IMAGE="diplicityreactregistry.azurecr.io/service:latest"
DOCKER_REGISTRY_URL="https://diplicityreactregistry.azurecr.io"

# Set the container configuration
az webapp config container set \
 --name $WEB_APP_NAME \
 --resource-group $RESOURCE_GROUP \
 --docker-custom-image-name $DOCKER_IMAGE \
 --docker-registry-server-url $DOCKER_REGISTRY_URL
