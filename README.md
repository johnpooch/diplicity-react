# Diplicity React

Welcome to the Diplicity React project! This is a web version of the classic Diplomacy board game. This project is maintained voluntarily by members of the online Diplomacy board game community.

## Get involved

We are looking for developers to get involved with the project. If you want to contribute, come say hi on the [Diplomacy Discord](chttps://discord.gg/QETtwGR).

## Project Overview

Diplicity React is a React-based web application which talks to a Django REST API to manage game state, player actions, and other game-related functionalities.

- **Application Deployment**: [Diplicity React App](https://blue-cliff-00777a403.4.azurestaticapps.net/)

## Technologies Used

- **React**: A JavaScript library for building user interfaces.
- **TypeScript**: A typed superset of JavaScript that compiles to plain JavaScript.
- **Vite**: A fast build tool and development server for modern web projects.
- **Material UI**: A popular React UI framework for building responsive and accessible user interfaces.
- **Storybook**: A tool for developing UI components in isolation.
- **Django**: A Python-based web framework for building robust and scalable web applications.
- **Celery**: A task queue system for running background tasks.

## Getting Started

### Prerequisites

Developing using Docker is the recommended way to run the application.

Download and install Docker Desktop from [here](https://www.docker.com/products/docker-desktop/).

You will also need to get a bunch of secrets. See the [.env.example](.env.example) file for more information.

### Getting started

1. Clone the repository:

   ```sh
   git clone https://github.com/johnpooch/diplicity-react.git
   cd diplicity-react
   ```

2. Start the containers

   ```sh
   docker compose up
   ```

3. To run Storybook, navigate to `/packages/web` and use the following command:

   ```sh
   npm run storybook
   ```

   Storybook will be available at `http://localhost:6006`.

## Developing on Android

### Developing in web browser

1. Navigate to the `native` package

   ```sh
   cd packages/native
   ```

2. Run Metro

   ```sh
   npx expo start
   ```

### Developing on Android device

Follow the instructions here:
https://docs.expo.dev/get-started/set-up-your-environment/?mode=development-build

1. Navigate to the `native` packge

   ```sh
   cd packages/native
   ```

2. Run build command

   ```sh
   eas build --platform android --profile development
   ```
