# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## !!! VERY IMPORTANT PRECURSOR - READ THIS FIRST !!!

**Under no circumstances should you agree with any assertion or claim without providing concrete, evidence-based reasoning.**

- **Evidence-Based Reasoning is Paramount:** For every claim, deduction, or inference, you **must** provide supporting evidence from the related context.
- **Corroborate All Findings:** Before proceeding with any chain of facts or thoughts, corroborate your findings, deductions, and inferences using the following format:
  `Based on what I found <here [and here ...]>, <yes/no | deductions> because <why>`.
- **Avoid Assumptions:** Never assume or guess. If information is unavailable, state it clearly. Do not assume correctness or incorrectness of any party (user or AI).
- **Logic, Facts, and Conclusive Evidence:** It is **PARAMOUNT** that you utilize logic, facts, and conclusive evidence at all times, rather than establishing blind trust or fulfilling requests without justification.

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
- **UI Components**: Transitioning from Material UI to shadcn/ui with Tailwind CSS
- **Testing**: Vitest + Testing Library
- **Build**: Vite with TypeScript compilation

### Frontend Style Guide

#### Tailwind CSS

When writing Tailwind CSS classes, follow these principles:

- **Avoid Unnecessary Classes**: Only add Tailwind classes that are actually needed for the design. Remove redundant or default values.
- **Keep It Minimal**: Prefer fewer, more intentional classes over verbose combinations.
- **Examples of unnecessary classes to avoid**:
  - `min-w-0` when the element already has appropriate width constraints
  - `flex-shrink-0` when shrinking behavior is already handled
  - `h-8 w-8` when `size="icon"` already sets dimensions
  - `ml-4` when `gap` utilities already handle spacing
  - `className="h-4 w-4"` on icons when the default size is appropriate
- **Trust Component Defaults**: shadcn/ui components have sensible defaults; only override when necessary

### Backend Structure (`/service/`)
- **Framework**: Django with Django REST Framework
- **API**: RESTful API with camel case conversion
- **Authentication**: JWT tokens with Google OAuth integration
- **Database**: PostgreSQL with Django ORM
- **Background Tasks**: Management commands for game resolution

## Best Practices

### General Development Guidelines

1. **Follow existing code patterns and conventions** - Consistency is key
2. **Use TypeScript for type safety** - Never use `any` types
3. **Run linting before submitting changes** - Fix all violations properly
   - Frontend: `npm run lint` (only on changed files when possible)
   - Backend: Use appropriate Python linters
4. **Run tests to validate changes** - Do not run full test suite
   - Always run single test files at a time for faster feedback
   - Frontend: `npm run test <filename>`
   - Backend: `docker compose run --rm service python3 -m pytest <test_file> -v`
5. **Never disable lint violations** - Fix the root cause instead
   - DO NOT use `eslint-disable`, `ts-ignore`, or similar suppression comments
   - If you cannot resolve a lint issue, explain what you tried and ask for guidance
   - The only acceptable outcomes are: the violation is properly fixed OR you report the issue
6. **Prefer composition over effects** - Minimize useEffect usage in React
7. **Use proper error handling** - Catch and handle errors appropriately
8. **Write tests alongside features** - Not as an afterthought

### Frontend Best Practices

1. **Component Design**:
   - Check for existing components before creating new ones
   - Keep components under 200 lines
   - Use compound component patterns for complex UIs

2. **Data Management**:
   - Use TanStack Query for new data fetching features
   - Always validate API responses with Zod schemas
   - Use `parseOnlyInDev` pattern to prevent production crashes

3. **Forms**:
   - Use React Hook Form for all new forms
   - Integrate Zod for validation
   - Avoid manual form state management

4. **React Patterns**:
   - Minimize useEffect usage - prefer derived state and event handlers
   - Use React 19 features (Context as provider, no forwardRef)
   - Let React 19 handle memoization automatically

### Backend Best Practices

Follow the Django patterns already established in the codebase (see Backend Development Guidelines section below).

## Testing

### Frontend Tests

Navigate to `/packages/web` and run:
```bash
npm run test              # Run all tests
npm run test <filename>   # Run specific test file (preferred)
```

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
