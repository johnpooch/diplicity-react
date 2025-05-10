# Task Queue

## Overview

The service needs to be able to run asynchronous tasks, such as sending
notifications, processing game phases, and other long-running operations. To
support this, we use a Celery worker with Azure Service Bus as the message
broker.

**Note** Azure Service Bus is used in both production and development.

## Workflow

- A request is triggered in the Django application which requires a long-running
  task.
- The task is added to the Celery task queue.
- The task is serialized and sent to the Azure Service Bus queue.
- The Celery worker picks up the task from the queue and processes it.
- The worker sends the result back to the Django application.

## Task Model

A `Task` model is used to represent a Celery task in the database.

## Testing

The following steps can be used to test the task queue:

Send a POST request to the `/tasks/` endpoint:

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/tasks/" -Method POST
```

The request should return a 201 Created response with the task ID in the
response body:

```json
{
  "id": "1234567890",
  "status": "PENDING"
}
```

The task ID can be used to check the status of the task in the database.

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/tasks/1234567890/" -Method GET
```

The request should return a 200 OK response with the task status in the
response body:

```json
{
  "id": "1234567890",
  "status": "COMPLETED"
}
```

**Note** this endpoint can also be used to test the production deployment.

**Note** this test can be executed using a docker container:

```bash
docker-compose up diplicity-task-test --build --watch
```
