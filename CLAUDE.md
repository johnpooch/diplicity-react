# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Diplicity React is a full-stack web application for the classic Diplomacy board game. The project consists of:

- **Frontend**: React + TypeScript web app using Material UI, Redux Toolkit, and Vite
- **Backend**: Django REST API with PostgreSQL database
- **Architecture**: Microservices with Docker containers

## Development Setup

### Prerequisites
- Docker and Docker Desktop
- Environment variables (see .env.example)

### Starting the Application
```bash
docker compose up
```

This starts all services:
- Web frontend at http://localhost:5173
- Django API at http://localhost:8000
- PostgreSQL database at http://localhost:5432

## Key Commands

### Frontend (React/TypeScript)
Navigate to `/packages/web` for these commands:
```bash
npm run dev          # Development server
npm run build        # Production build
npm run lint         # ESLint
npm run test         # Vitest tests
npm run storybook    # Storybook at http://localhost:6006
```

### Backend (Django)
Navigate to `/service` for these commands:
```bash
docker compose run --rm service python3 manage.py migrate
docker compose run --rm service python3 manage.py runserver
```

### Docker Services
```bash
docker compose up codegen      # Generate API client from OpenAPI schema
docker compose up test-service # Run Django tests in container
```

## Code Architecture

### Frontend Structure (`/packages/web/`)
- **State Management**: Redux Toolkit with RTK Query for API calls
- **Routing**: React Router for navigation
- **UI Components**: Material UI with custom theme
- **Testing**: Vitest + Testing Library
- **Build**: Vite with TypeScript compilation

### Backend Structure (`/service/`)
- **Framework**: Django with Django REST Framework
- **API**: RESTful API with camel case conversion
- **Authentication**: JWT tokens with Google OAuth integration
- **Database**: PostgreSQL with Django ORM
- **Background Tasks**: Management commands for game resolution

## Testing


### Backend Tests

To run all backend tests:
```bash
docker compose run --rm service python3 -m pytest -v
```

To run a specific test file:
```bash
docker compose run --rm service python3 -m pytest game/tests/test_game_create.py -v
```

To run a specific test function:
```bash
docker compose run --rm service python3 -m pytest game/tests/test_game_create.py::test_create_game_success -v 
```

To run a specific test method of a test class:
```bash
docker compose run --rm service python3 -m pytest game/tests/test_game_create.py::TestClass::test_create_game_success -v 
```

## API Development

The API schema is auto-generated using DRF Spectacular:
```bash
docker compose up codegen
```

This generates OpenAPI schema and TypeScript client code for the frontend.

## Backend Development Guidelines

### Style Guide

#### General

- **Comments**: Do not add docstrings or comments.

#### Project Structure

The project is broken down into apps, where each app is responsible for a single core concept, e.g. `game`, `order`, `user_profile`, etc.

**Standard App Structure:**
Each app should contain these files:
- `models.py` - Data models with custom QuerySets and Managers
- `serializers.py` - DRF serializers using base `Serializer` class
- `views.py` - API views using DRF generics
- `urls.py` - URL routing
- `conftest.py` - Test fixtures (pytest fixtures)
- `tests.py` - Test cases focusing on API endpoints
- `admin.py` - Django admin configuration
- `utils.py` - Helper functions (when needed)

Apps must adhere to the following guidelines:

**Views**

Views should be simple and should leverage DRF generic views where appropriate. The `check_permissions` method should be used to carry out initial permission checks for the request. Mixins should be used to provide context to the views and serializers.

Follow this pattern:
- Use `generics.ListAPIView`, `generics.CreateAPIView`, `generics.RetrieveAPIView`, etc.
- Apply permission classes: `[permissions.IsAuthenticated, IsActiveGame, IsGameMember]`
- Use mixins from `common.views` for shared functionality (`SelectedGameMixin`, `CurrentGameMemberMixin`, etc.)
- Keep view logic minimal - delegate to managers and querysets

**Serializers**

Serializers should use the standard `Serializer` base class over the `ModelSerializer` base class. They should be kept as simple as possible.

Follow this pattern:
- Explicitly define fields rather than using `ModelSerializer` auto-generation
- Use `read_only=True` for computed/derived fields
- Import and compose other serializers for related objects
- Keep validation logic in custom `validate_*` methods
- Use context from views (`self.context["request"]`, `self.context["game"]`, etc.)

**Models**

Models have two responsibilities: (1) defining the fields of the data structure; (2) defining properties for conveniently accessing related entities and deriving data.

Query optimization code should be defined on a custom QuerySet class. Follow this pattern:

```python
class ModelQuerySet(models.QuerySet):
    def business_filter_method(self, param):
        return self.filter(...)

    def with_related_data(self):
        return self.select_related(...).prefetch_related(...)

class ModelManager(models.Manager):
    def get_queryset(self):
        return ModelQuerySet(self.model, using=self._db)

    def business_filter_method(self, param):
        return self.get_queryset().business_filter_method(param)

    def with_related_data(self):
        return self.get_queryset().with_related_data()

class Model(BaseModel):
    objects = ModelManager()

    @property
    def derived_property(self):
        return self.some_calculation()
```

**Testing**

Test fixtures should exist in the app's `conftest.py` file rather than in the test file itself.

Follow this testing pattern:
- Create pytest fixtures in `conftest.py` that return callable factory functions
- Focus on API endpoint testing rather than unit testing individual methods
- Use fixtures like `@pytest.fixture def factory_function(db, other_fixtures): def _create(...): return Model.objects.create(...); return _create`
- Test comprehensive endpoint behavior including permissions, validation, and data transformations
- Add performance tests to ensure N+1 query issues are avoided
- For complex logic in utils files, create separate test classes

**Utils**

Logic which does not naturally belong in the serializers, views, or models should be defined in the `utils.py` file.
