# Diplicity React

Welcome to the Diplicity React project! This is a web version of the classic Diplomacy board game. This project is maintained voluntarily by members of the online Diplomacy board game community.

## Get involved

We are looking for developers to get involved with the project. If you want to contribute, come say hi on the [Diplomacy Discord](chttps://discord.gg/QETtwGR).

## Project Overview

Diplicity React is a React-based web application which integrates with a Django REST API to manage game state, player actions, and other game-related functionalities.

- **Live Deployment**: [Diplicity](https://diplicity.com)

## Getting Started

### Prerequisites

#### Secrets

Google sign in and other functionality will not work locally unless you have the required secrets. See the [.env.example](.env.example) file for more information.

#### Docker

Developing using Docker is the recommended way to run the application.

Download and install Docker Desktop from [here](https://www.docker.com/products/docker-desktop/).

### Running the project locally

Open a terminal window and run the following command to build the entire project:
```bash
docker compose up service web db phase-resolver
```

**Note** The terminal window will show logs from all of the containers which is useful for debugging.

The experience will now be available in your browser at `http://localhost:5173/`.

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
