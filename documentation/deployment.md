# Deployment and CI/CD Pipeline

## Overview

The project is comprised of the following components:

- **React web app**: The web app is built using a GitHub Actions workflow and is deployed as an Azure Static Web App.

- **Django service**: The service is built using a Dockerfile. Using a GitHub Actions workflow, a docker image is built and pushed to an Azure Container Registry and then deployed to an Azure Web App.

- **Django worker**: The worker is built using a Dockerfile. Using a GitHub Actions workflow, a docker image is built and pushed to an Azure Container Registry and then deployed to an Azure Web App.

- **PostgreSQL database**: The database is deployed as an Azure Database for PostgreSQL.

- **Service bus**: The service bus is deployed as an Azure Service Bus. Note, this is used in local development as well as in production.

- **Key vault**: The key vault is deployed as an Azure Key Vault. This is used to store secrets and shared configuration.

Details of the various components are provided in `.azure/settings.json`.