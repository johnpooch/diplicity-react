import type { Meta, StoryObj } from "@storybook/react";
import { HomeLayout } from "./HomeLayout";
import { Navigation } from "./Navigation";
import { AppBar } from "./AppBar.new";
import { Button } from "@/components/ui/button";
import { Icon, IconName } from "./Icon";
import { navigationItems } from "../navigation/navigationItems";
import { GameCard } from "./GameCard.new";
import { InfoPanel } from "./InfoPanel.new";

/**
 * HomeLayout is a responsive app shell that provides a flexible three-column
 * layout with optional bottom navigation. It handles all responsive behavior
 * declaratively through the breakpoints prop.
 */
const meta = {
  title: "Layout/HomeLayout",
  component: HomeLayout,
  parameters: {
    layout: "fullscreen",
  },
} satisfies Meta<typeof HomeLayout>;

export default meta;
type Story = StoryObj<typeof meta>;

// Helper to create navigation items with active state
const createNavItems = (activePath: string = "/") =>
  navigationItems.map(item => ({
    ...item,
    isActive: item.path === activePath,
  }));

const MapComponent = () => (
  <svg viewBox="0 0 800 600" style={{ width: "100%", height: "100%" }}>
    <defs>
      <pattern
        id="horizontalStripes"
        width="20"
        height="20"
        patternUnits="userSpaceOnUse"
      >
        <rect width="20" height="10" fill="#e2e8f0" />
        <rect y="10" width="20" height="10" fill="#cbd5e1" />
      </pattern>
    </defs>
    <rect width="800" height="600" fill="url(#horizontalStripes)" />
    <text
      x="400"
      y="300"
      fontSize="48"
      fill="#64748b"
      textAnchor="middle"
      dominantBaseline="middle"
    >
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

const mockGames = [
  {
    game: {
      id: "game-1",
      name: "European Diplomacy Championship",
      private: false,
      members: mockMembers,
      canJoin: false,
      movementPhaseDuration: "24 hours" as const,
    },
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
    game: {
      id: "game-2",
      name: "New Game - Need Players!",
      private: false,
      members: mockMembers.slice(0, 2),
      canJoin: true,
      movementPhaseDuration: "48 hours" as const,
    },
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
    game: {
      id: "game-3",
      name: "Private Tournament Match",
      private: true,
      members: mockMembers,
      canJoin: false,
      movementPhaseDuration: "24 hours" as const,
    },
    variant: {
      name: "Classic",
      id: "classical",
    },
    phase: {
      season: "Fall",
      year: 1910,
      type: "Retreat",
      scheduledResolution: new Date(
        Date.now() + 2 * 60 * 60 * 1000
      ).toISOString(),
    },
  },
  {
    game: {
      id: "game-4",
      name: "Quick Match",
      private: false,
      members: mockMembers.slice(0, 3),
      canJoin: false,
      movementPhaseDuration: undefined,
    },
    variant: {
      name: "Classic",
      id: "classical",
    },
    phase: {
      season: "Spring",
      year: 1902,
      type: "Movement",
      scheduledResolution: "",
    },
  },
];

const GameListContent = () => (
  <div>
    {mockGames.map(gameData => (
      <GameCard
        key={gameData.game.id}
        game={gameData.game}
        variant={gameData.variant}
        phase={gameData.phase}
        map={<MapComponent />}
        onClickGame={(id: string) => console.log("Game clicked", id)}
        onClickGameInfo={(id: string) => console.log("Game info clicked", id)}
        onClickPlayerInfo={(id: string) => console.log("Player info clicked", id)}
        onClickJoinGame={(id: string) => console.log("Join game clicked", id)}
      />
    ))}
  </div>
);


export const Default: Story = {
  args: {
    left: (
      <Navigation
        items={createNavItems("/")}
        variant="sidebar"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
    center: (
      <>
        <AppBar
          title="My Games"
          leftAction={
            <Button
              variant="ghost"
              size="icon"
              onClick={() => console.log("Back clicked")}
              aria-label="Go back"
            >
              <Icon name={IconName.Back} variant="lucide" size={20} />
            </Button>
          }
          rightAction={
            <Button
              variant="ghost"
              size="icon"
              onClick={() => console.log("Menu clicked")}
              aria-label="Open menu"
            >
              <Icon name={IconName.Menu} variant="lucide" size={20} />
            </Button>
          }
        />
        <GameListContent />
      </>
    ),
    right: <InfoPanel />,
    bottom: (
      <Navigation
        items={createNavItems("/")}
        variant="bottom"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
  },
};
