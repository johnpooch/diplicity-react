# Diplicity React

Welcome to the Diplicity React project! This is a web version of the classic Diplomacy board game. This project is maintained voluntarily by members of the online Diplomacy board game community.

## Get involved

We are looking for developers to get involved with the project. If you want to contribute, come say hi on the [Diplomacy Discord](https://discord.gg/2TkZbBRPW), and see [DEVELOPER.md](DEVELOPER.md) for the contributor setup guide.

## Project Overview

Diplicity React is a React-based web application which integrates with a Django REST API to manage game state, player actions, and other game-related functionalities.

- **Live Deployment**: [Diplicity](https://diplicity.com)

## Getting Started

See [DEVELOPER.md](DEVELOPER.md) for the full setup guide, including how to create a local user and access the admin panel.

### Prerequisites

#### Docker

Developing using Docker is the recommended way to run the application.

Download and install Docker Desktop from [here](https://www.docker.com/products/docker-desktop/).

No secrets or `.env` file are needed to run the app locally. Optional features (Google sign-in, push notifications, error tracking) need real credentials — see [When you need more keys](DEVELOPER.md#when-you-need-more-keys).

### Running the project locally

Open a terminal window and run the following command to build the entire project:
```bash
docker compose up service web db worker phase-resolver
```

**Note** The terminal window will show logs from all of the containers which is useful for debugging.

The experience will now be available in your browser at `http://localhost:5173/`.

To log in you first need a local user — the app has no seeded account and your diplicity.com account does not exist locally. Create one with:
```bash
docker compose exec service python manage.py create_test_user
```
Then log in with `test@example.com` / `password`. See [DEVELOPER.md](DEVELOPER.md) for creating an admin user and manual testing.

## Testing

### Running Backend Tests

The Django backend includes a comprehensive test suite.

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
