#!/usr/bin/env vite-node
// Declares the screen matrix captured by scripts/screenshot-diff/capture.mjs.
//
// Game screens are expanded from the MSW fixtures rather than listed by hand,
// so a new fixture in src/mocks/fixtures/games.ts gains screenshot coverage
// without touching this file.

import { fixtureByGameId } from "../../src/mocks/fixtures/index.ts";

export const viewports = [
  { name: "mobile", width: 390, height: 844 },
  { name: "desktop", width: 1280, height: 800 },
];

const loggedOutScreens = [
  { name: "login", path: "/" },
  { name: "register", path: "/register" },
  { name: "forgot-password", path: "/forgot-password" },
  { name: "check-email", path: "/check-email" },
  { name: "verify-email", path: "/verify-email" },
  { name: "reset-password", path: "/reset-password" },
];

const homeScreens = [
  { name: "my-games", path: "/" },
  { name: "find-games", path: "/find-games" },
  { name: "create-game", path: "/create-game" },
  { name: "account", path: "/account" },
  { name: "delete-account", path: "/delete-account" },
  { name: "community", path: "/community" },
  { name: "learn-to-play", path: "/learn-to-play" },
  { name: "tutorial", path: "/learn-to-play/tutorial" },
  { name: "variants", path: "/variants" },
  { name: "variants-create", path: "/variants/create" },
];

const pendingGameScreens = gameId => [
  { name: `game-info__${gameId}`, path: `/game-info/${gameId}` },
  { name: `player-info__${gameId}`, path: `/player-info/${gameId}` },
  { name: `nation-preference__${gameId}`, path: `/nation-preference/${gameId}` },
];

const phaseGameScreens = (gameId, phaseId, fixture) => {
  const base = `/game/${gameId}/phase/${phaseId}`;
  const screens = [
    { name: `board__${gameId}`, path: base },
    { name: `orders__${gameId}`, path: `${base}/orders` },
    { name: `chat__${gameId}`, path: `${base}/chat` },
    { name: `game-detail-info__${gameId}`, path: `${base}/game-info` },
    { name: `variant-details__${gameId}`, path: `${base}/game-info/variant` },
    { name: `player-info__${gameId}`, path: `${base}/player-info` },
  ];
  if ((fixture.drawProposals ?? []).length > 0) {
    screens.push({
      name: `draw-proposals__${gameId}`,
      path: `${base}/draw-proposals`,
    });
  }
  return screens;
};

const gameScreens = () =>
  Object.entries(fixtureByGameId).flatMap(([gameId, fixture]) => {
    const phases = fixture.phases ?? [];
    if (phases.length === 0) return pendingGameScreens(gameId);
    const latest = phases[phases.length - 1];
    return phaseGameScreens(gameId, latest.id, fixture);
  });

export const screens = [
  ...loggedOutScreens.map(screen => ({ ...screen, loggedOut: true })),
  ...homeScreens.map(screen => ({ ...screen, loggedOut: false })),
  ...gameScreens().map(screen => ({ ...screen, loggedOut: false })),
];
