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
python3 manage.py migrate        # Run database migrations
python3 manage.py runserver     # Development server
python3 -m pytest              # Run tests
python3 manage.py resolve_due_phases  # Game phase resolution
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

### Frontend Tests
```bash
cd packages/web && npm run test
```

### Backend Tests
```bash
cd service && python -m pytest
```
or via Docker:
```bash
docker compose up test-service
```

## API Development

The API schema is auto-generated using DRF Spectacular:
```bash
docker compose up codegen
```

This generates OpenAPI schema and TypeScript client code for the frontend.