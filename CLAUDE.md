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

### Key Backend Modules
- `game/models/`: Core game entities (Game, Phase, Order, etc.)
- `game/services/`: Business logic layer
- `game/views/`: API endpoints
- `game/serializers/`: API data transformation
- `game/management/commands/`: Background tasks

### Game Logic
- Games progress through phases (Spring, Fall, Retreat, Adjustment)
- Orders are submitted by players and resolved automatically
- Phase resolution runs every 60 seconds via management command
- Game state is managed through Django models with proper relationships

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

Apps must adhere to the following guidelines:

**Views**

Views should be simple and should leverage DRF generic views where appropriate. The `check_permissions` method should be used to carry out initial permission checks for the request. Mixins should be used to provide context to the views and serializers.

**Serializers**

Serializers should use the standard `Serializer` base class over the `ModelSerializer` base class. They should be kept as simple as possible.

**Models**

Models have two responsibilities: (1) defining the fields of the data structure; (2) defining properties for conveniently accessing related entities and deriving data.

Query optimization code should be defined on a custom QuerySet class.

**Testing**

Test fixtures should exist in the app's `conftest.py` file rather than in the test file itself.

For most apps, testing the API endpoints is sufficient. Tests should comprehensively cover the behaviour of the endpoints. Performance tests should be added to ensure that N+1 query issues are avoided.

For complex logic, e.g. logic that exists in util files, separate test classes should be added.

**Utils**

Logic which does not naturally belong in the serializers, views, or models should be defined in the `utils.py` file.
