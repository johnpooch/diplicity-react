import type { Meta, StoryObj } from "@storybook/react";
import { action } from "@storybook/addon-actions";
import { MyGames } from "./MyGames.new";

const meta = {
  title: "Screens/MyGames",
  component: MyGames,
  parameters: {
    layout: "fullscreen",
  },
} satisfies Meta<typeof MyGames>;

export default meta;
type Story = StoryObj<typeof meta>;

const mockMembers = [
  {
    id: 1,
    name: "Player 1",
    picture: null,
    nation: "Austria",
    isCurrentUser: false,
  },
  {
    id: 2,
    name: "Player 2",
    picture: null,
    nation: "England",
    isCurrentUser: false,
  },
  {
    id: 3,
    name: "Player 3",
    picture: null,
    nation: "France",
    isCurrentUser: false,
  },
  {
    id: 4,
    name: "Player 4",
    picture: null,
    nation: "Germany",
    isCurrentUser: false,
  },
];

const mockGames = [
  {
    id: "game-1",
    name: "European Diplomacy Championship",
    private: false,
    members: mockMembers,
    canJoin: false,
    movementPhaseDuration: "24 hours",
    status: "active",
    variant: {
      name: "Classic",
      id: "classical",
    },
    phase: {
      season: "Spring",
      year: 1905,
      type: "Movement",
      scheduledResolution: new Date(
        Date.now() + 6 * 60 * 60 * 1000
      ).toISOString(),
    },
  },
  {
    id: "game-2",
    name: "Quick Evening Game",
    private: false,
    members: mockMembers,
    canJoin: false,
    movementPhaseDuration: "24 hours",
    status: "active",
    variant: {
      name: "Classic",
      id: "classical",
    },
    phase: {
      season: "Fall",
      year: 1902,
      type: "Movement",
      scheduledResolution: new Date(
        Date.now() + 12 * 60 * 60 * 1000
      ).toISOString(),
    },
  },
  {
    id: "game-3",
    name: "New Game - Need Players!",
    private: false,
    members: mockMembers.slice(0, 2),
    canJoin: true,
    movementPhaseDuration: "48 hours",
    status: "pending",
    variant: {
      name: "Classic",
      id: "classical",
    },
    phase: {
      season: "Spring",
      year: 1901,
      type: "Movement",
      scheduledResolution: new Date(
        Date.now() + 26 * 60 * 60 * 1000
      ).toISOString(),
    },
  },
  {
    id: "game-4",
    name: "Weekend Tournament",
    private: true,
    members: mockMembers.slice(0, 3),
    canJoin: false,
    movementPhaseDuration: "24 hours",
    status: "pending",
    variant: {
      name: "Classic",
      id: "classical",
    },
    phase: {
      season: "Spring",
      year: 1901,
      type: "Movement",
      scheduledResolution: new Date(
        Date.now() + 48 * 60 * 60 * 1000
      ).toISOString(),
    },
  },
  {
    id: "game-5",
    name: "Historic Battle - Finished",
    private: false,
    members: mockMembers,
    canJoin: false,
    movementPhaseDuration: "24 hours",
    status: "completed",
    variant: {
      name: "Classic",
      id: "classical",
    },
    phase: {
      season: "Fall",
      year: 1918,
      type: "Movement",
      scheduledResolution: new Date(
        Date.now() - 48 * 60 * 60 * 1000
      ).toISOString(),
    },
  },
  {
    id: "game-6",
    name: "Another Completed Game",
    private: false,
    members: mockMembers,
    canJoin: false,
    movementPhaseDuration: "48 hours",
    status: "completed",
    variant: {
      name: "Classic",
      id: "classical",
    },
    phase: {
      season: "Spring",
      year: 1920,
      type: "Movement",
      scheduledResolution: new Date(
        Date.now() - 72 * 60 * 60 * 1000
      ).toISOString(),
    },
  },
];

export const WithActiveGames: Story = {
  args: {
    selectedStatus: "active",
    onStatusChange: action("status-changed"),
    isLoading: false,
    games: mockGames,
    onClickGame: action("game-clicked"),
    onClickGameInfo: action("game-info-clicked"),
    onClickPlayerInfo: action("player-info-clicked"),
    onClickJoinGame: action("join-game-clicked"),
  },
};

export const WithPendingGames: Story = {
  args: {
    selectedStatus: "pending",
    onStatusChange: action("status-changed"),
    isLoading: false,
    games: mockGames,
    onClickGame: action("game-clicked"),
    onClickGameInfo: action("game-info-clicked"),
    onClickPlayerInfo: action("player-info-clicked"),
    onClickJoinGame: action("join-game-clicked"),
  },
};

export const WithCompletedGames: Story = {
  args: {
    selectedStatus: "completed",
    onStatusChange: action("status-changed"),
    isLoading: false,
    games: mockGames,
    onClickGame: action("game-clicked"),
    onClickGameInfo: action("game-info-clicked"),
    onClickPlayerInfo: action("player-info-clicked"),
    onClickJoinGame: action("join-game-clicked"),
  },
};

export const Loading: Story = {
  args: {
    selectedStatus: "active",
    onStatusChange: action("status-changed"),
    isLoading: true,
    games: undefined,
    onClickGame: action("game-clicked"),
    onClickGameInfo: action("game-info-clicked"),
    onClickPlayerInfo: action("player-info-clicked"),
    onClickJoinGame: action("join-game-clicked"),
  },
};

export const EmptyActive: Story = {
  args: {
    selectedStatus: "active",
    onStatusChange: action("status-changed"),
    isLoading: false,
    games: mockGames.filter((g) => g.status === "pending"),
    onClickGame: action("game-clicked"),
    onClickGameInfo: action("game-info-clicked"),
    onClickPlayerInfo: action("player-info-clicked"),
    onClickJoinGame: action("join-game-clicked"),
  },
};

export const EmptyPending: Story = {
  args: {
    selectedStatus: "pending",
    onStatusChange: action("status-changed"),
    isLoading: false,
    games: mockGames.filter((g) => g.status === "active"),
    onClickGame: action("game-clicked"),
    onClickGameInfo: action("game-info-clicked"),
    onClickPlayerInfo: action("player-info-clicked"),
    onClickJoinGame: action("join-game-clicked"),
  },
};

export const EmptyCompleted: Story = {
  args: {
    selectedStatus: "completed",
    onStatusChange: action("status-changed"),
    isLoading: false,
    games: mockGames.filter((g) => g.status !== "completed"),
    onClickGame: action("game-clicked"),
    onClickGameInfo: action("game-info-clicked"),
    onClickPlayerInfo: action("player-info-clicked"),
    onClickJoinGame: action("join-game-clicked"),
  },
};
