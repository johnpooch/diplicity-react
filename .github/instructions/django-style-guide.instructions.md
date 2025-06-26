---
applyTo: '**/*.py'
---

# Django Style Guide

## Models

- Each model should be defined in its own file inside the `/models/` directory.
- Models should be exported in the `__init__.py` file of the `/models/` directory.
- Model file names should be in lowercase and use underscores to separate words (e.g., `user_profile.py`).
- Very little business logic should be defined in the model code. Instead, use the `/services/` directory for business logic.

## Views

- A views file should be created for each domain concept, e.g., `game`, `channel`, etc.
- The naming convention for views files is `<domain_concept>_view.py`, e.g., `game_view.py`, `channel_view.py`, etc.
- Each API operation should be defined by its own class-based view.
- All class-based views should inherit from `views.APIView`.
- The request data should be deserialized and validated using a `RequestSerializer` class defined within the view class.
- Query parameters should be validated using a `QuerySerializer` class defined within the view class.
- Views and serializers should not contain any business logic. Instead, use the `/services/` directory for business logic.
- Views should be exported in the `__init__.py` file of the `/views/` directory.
- The naming convention for views is `<DomainConcept><Operation>View`, e.g., `GameListView`, `GameDetailView`, etc.
- The `get` and `post` methods should be annotated with the `@extend_schema` decorator to provide OpenAPI documentation.

## Services

- A service file should be created for each domain concept, e.g., `game`, `channel`, etc.
- The naming convention for service files is `<domain_concept>_service.py`, e.g., `game_service.py`, `channel_service.py`, etc.
- Each service should be defined in its own file inside the `/services/` directory.
- Services should be exported in the `__init__.py` file of the `/services/` directory.
- The naming convention for services is `<DomainConcept>Service`, e.g., `GameService`, `ChannelService`, etc.
- Services should be defined as classes and should inherit from `BaseService`.
- Service methods should typically follow the API operation naming convention, e.g., `list`, `retrieve`, `create`, `update`, `delete`.
- All of the business logic should be defined in the service code.

## Serializers

- Serializers should be defined in the `/serializers/` directory.
- The naming convention for serializer files is `<domain_concept>_serializers.py`, e.g., `game_serializers.py`, `channel_serializers.py`, etc.
- Serializers should be exported in the `__init__.py` file of the `/serializers/` directory.
- Avoid using `SerializerMethodField`. Instead, annotate the queryset with the required data in the service layer.

## Tests

- Tests should be defined in the `/tests/` directory.
- The naming convention for test files is `test_<domain_concept>.py`, e.g., `test_game.py`, `test_channel.py`, etc.
- Each test file should contain tests for a single domain concept.
- The naming convention for test classes is `Test<DomainConcept><Operation>`, e.g., `TestGameList`, `TestGameDetail`, etc.
- The naming convention for test methods is `test_<description>`, e.g., `test_throws_404_if_game_does_not_exist`, `test_returns_200_if_game_exists`, etc.
- Tests should inherit from a base test class which provides common functionality for all tests.
- Tests should be integration tests that test the entire functionality by calling a single endpoint and asserting the response and the database state.
- Include tests for all possible error scenarios, such as unauthorized access, invalid input, and resource not found.
- Always validate both the HTTP response status code and the response body.
- Test both authenticated and unauthenticated scenarios for endpoints requiring user authentication.
- Use `force_authenticate` to simulate logged-in users in tests.
- For tasks scheduled with Celery or similar tools, verify that tasks are scheduled with the correct arguments and timing.
- Mock task execution and validate the expected outcomes.
- Use `setUp` methods to initialize common test data and configurations for each test class.
- Mock external dependencies (e.g., third-party APIs, services) in the `setUp` method using `unittest.mock.patch`.

## Imports

- Prefer importing modules over importing specific classes or functions, e.g.:
  - `from django.db import models` instead of `from django.db.models import Model`.
  - `from .. import services` instead of `from ..services import GameService`.