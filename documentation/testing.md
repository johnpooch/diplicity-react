# Testing

## Overview

The Diplicity React project uses **pytest** for testing the Django backend service. The test suite provides comprehensive coverage of the game logic, API endpoints, and business services.

## Backend Service

### Prerequisites

Ensure the database container is running when developing locally:

```bash
docker compose up db
```

### Test Execution

Navigate to the service directory and run the full test suite:

```bash
cd /service
python3 -m pytest
```