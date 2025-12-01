import type { Meta, StoryObj } from "@storybook/react";
import { GameCard } from "./GameCard.new";

const meta = {
  title: "Components/GameCard",
  component: GameCard,
  parameters: {
    layout: "fullscreen",
  },
} satisfies Meta<typeof GameCard>;

export default meta;
type Story = StoryObj<typeof meta>;

const MapComponent = () => (
  <svg viewBox="0 0 800 600" style={{ width: "100%", height: "100%" }}>
    <defs>
      <pattern id="horizontalStripes" width="20" height="20" patternUnits="userSpaceOnUse">
        <rect width="20" height="10" fill="#e2e8f0" />
        <rect y="10" width="20" height="10" fill="#cbd5e1" />
      </pattern>
    </defs>
    <rect width="800" height="600" fill="url(#horizontalStripes)" />
    <text x="400" y="300" fontSize="48" fill="#64748b" textAnchor="middle" dominantBaseline="middle">
      Map
    </text>
  </svg>
);

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

export const Default: Story = {
  args: {
    game: {
      id: "game-1",
      name: "European Diplomacy Championship",
      private: false,
      members: mockMembers,
      canJoin: false,
      movementPhaseDuration: "24 hours",
    },
    variant: {
      name: "Classic",
    },
    phase: {
      season: "Spring",
      year: 1905,
      type: "Movement",
      scheduledResolution: "in 6 hours",
    },
    map: <MapComponent />,
    onClickGame: id => console.log("Game clicked", id),
    onClickGameInfo: id => console.log("Game info clicked", id),
    onClickPlayerInfo: id => console.log("Player info clicked", id),
    onClickJoinGame: id => console.log("Join game clicked", id),
    onMenuClick: id => console.log("Menu clicked", id),
  },
};

export const WithJoinButton: Story = {
  args: {
    game: {
      id: "game-2",
      name: "New Game - Need Players!",
      private: false,
      members: mockMembers.slice(0, 2),
      canJoin: true,
      movementPhaseDuration: "48 hours",
    },
    variant: {
      name: "Classic",
    },
    phase: {
      season: "Spring",
      year: 1901,
      type: "Movement",
      scheduledResolution: "in 12 hours",
    },
    map: <MapComponent />,
    onClickGame: id => console.log("Game clicked", id),
    onClickGameInfo: id => console.log("Game info clicked", id),
    onClickPlayerInfo: id => console.log("Player info clicked", id),
    onClickJoinGame: id => console.log("Join game clicked", id),
    onMenuClick: id => console.log("Menu clicked", id),
  },
};

export const PrivateGame: Story = {
  args: {
    game: {
      id: "game-3",
      name: "Private Tournament Match",
      private: true,
      members: mockMembers,
      canJoin: false,
      movementPhaseDuration: "24 hours",
    },
    variant: {
      name: "Classic",
    },
    phase: {
      season: "Fall",
      year: 1910,
      type: "Retreat",
      scheduledResolution: "in 2 hours",
    },
    map: <MapComponent />,
    onClickGame: id => console.log("Game clicked", id),
    onClickGameInfo: id => console.log("Game info clicked", id),
    onClickPlayerInfo: id => console.log("Player info clicked", id),
    onClickJoinGame: id => console.log("Join game clicked", id),
    onMenuClick: id => console.log("Menu clicked", id),
  },
};

export const ResolveWhenReady: Story = {
  args: {
    game: {
      id: "game-4",
      name: "Quick Game",
      private: false,
      members: mockMembers,
      canJoin: false,
      movementPhaseDuration: undefined,
    },
    variant: {
      name: "Classic",
    },
    phase: {
      season: "Spring",
      year: 1902,
      type: "Movement",
      scheduledResolution: "when ready",
    },
    map: <MapComponent />,
    onClickGame: id => console.log("Game clicked", id),
    onClickGameInfo: id => console.log("Game info clicked", id),
    onClickPlayerInfo: id => console.log("Player info clicked", id),
    onClickJoinGame: id => console.log("Join game clicked", id),
    onMenuClick: id => console.log("Menu clicked", id),
  },
};

export const WithMapImage: Story = {
  args: {
    game: {
      id: "game-5",
      name: "European Diplomacy Championship",
      private: false,
      members: mockMembers,
      canJoin: false,
      movementPhaseDuration: "24 hours",
    },
    variant: {
      name: "Classic",
    },
    phase: {
      season: "Spring",
      year: 1905,
      type: "Movement",
      scheduledResolution: "in 6 hours",
    },
    map: <MapComponent />,
    onClickGame: id => console.log("Game clicked", id),
    onClickGameInfo: id => console.log("Game info clicked", id),
    onClickPlayerInfo: id => console.log("Player info clicked", id),
    onClickJoinGame: id => console.log("Join game clicked", id),
    onMenuClick: id => console.log("Menu clicked", id),
  },
};

export const MinimalInfo: Story = {
  args: {
    game: {
      id: "game-6",
      name: "Simple Game",
      private: false,
      members: [],
      canJoin: false,
      movementPhaseDuration: undefined,
    },
    variant: {
      name: "Classic",
    },
    phase: {
      season: "Spring",
      year: 1901,
      type: "Movement",
      scheduledResolution: "in 24 hours",
    },
    map: <MapComponent />,
    onClickGame: id => console.log("Game clicked", id),
    onClickGameInfo: id => console.log("Game info clicked", id),
    onClickPlayerInfo: id => console.log("Player info clicked", id),
    onClickJoinGame: id => console.log("Join game clicked", id),
    onMenuClick: id => console.log("Menu clicked", id),
  },
};
