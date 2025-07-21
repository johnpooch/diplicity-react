# Deployment and CI/CD Pipeline

## Overview

The project is comprised of the following components:

- **React web app**: The web app is built using a GitHub Actions workflow and is deployed as an Azure Static Web App.

- **Django service**: The service is built using a Dockerfile. Using a GitHub Actions workflow, a docker image is built and pushed to an Azure Container Registry and then deployed to an Azure Web App.

- **CRON job**: The CRON job is a simple Python script that runs every minute and resolves any due phases.

- **PostgreSQL database**: The database is deployed as an Azure Database for PostgreSQL.

- **Key vault**: The key vault is deployed as an Azure Key Vault. This is used to store secrets and shared configuration.

Details of the various components are provided in `.azure/settings.json`.