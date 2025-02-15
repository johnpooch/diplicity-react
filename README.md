# Diplicity React

Welcome to the Diplicity React project! This project is a web client for [Diplicity](https://github.com/zond/diplicity). This project is maintained voluntarily by members of the online Diplomacy board game community.

## Get involved

We are looking for developers to get involved with the project. If you want to contribute, come say hi on the [Diplomacy Discord](chttps://discord.gg/QETtwGR).

## Project Overview

Diplicity React is a React-based web application that allows users to play the Diplomacy board game online. The application communicates with the diplicity API to manage game state, player actions, and other game-related functionalities.

- **API Link**: [diplicity API](https://github.com/zond/diplicity)
- **Application Deployment**: [Diplicity React App](https://blue-cliff-00777a403.4.azurestaticapps.net/)
- **Storybook Deployment**: [Diplicity React Storybook](https://nice-sand-001bca703.4.azurestaticapps.net/)

## Technologies Used

- **React**: A JavaScript library for building user interfaces.
- **TypeScript**: A typed superset of JavaScript that compiles to plain JavaScript.
- **Vite**: A fast build tool and development server for modern web projects.
- **Material UI**: A popular React UI framework for building responsive and accessible user interfaces.
- **Storybook**: A tool for developing UI components in isolation.

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed on your machine:

- Node.js (v14 or higher)
- NPM (v6 or higher)

### Getting started

1. Clone the repository:

   ```sh
   git clone https://github.com/johnpooch/diplicity-react.git
   cd diplicity-react
   ```

2. Install the dependencies:

   ```sh
   npm install
   ```

3. Start the development server:

   ```sh
    npm run dev
   ```

   The application will be available at `http://localhost:5173`.

4. To run Storybook, use the following command:

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
