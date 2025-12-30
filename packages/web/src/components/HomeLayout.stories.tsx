import type { Meta, StoryObj } from "@storybook/react";
import { action } from "@storybook/addon-actions";
import { HomeLayout } from "./HomeLayout";
import { Navigation } from "./Navigation";
import { AppBar } from "./AppBar.new";
import { Button } from "@/components/ui/button";
import { Icon, IconName } from "./Icon";
import { homeNavigationItems } from "../navigation/navigationItems";
import { GameCard } from "./GameCard.new";
import { InfoPanel } from "./InfoPanel.new";
import { CreateGame, VariantForSelector } from "../screens/Home/CreateGame.new";
import { MyGames } from "../screens/Home/MyGames.new";
import { Profile } from "../screens/Home/Profile.new";
import { FindGames } from "../screens/Home/FindGames.new";
import { SandboxGames } from "../screens/Home/SandboxGames.new";

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
  homeNavigationItems.map(item => ({
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

const mockMyGames = [
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
        onClickPlayerInfo={(id: string) =>
          console.log("Player info clicked", id)
        }
        onClickJoinGame={(id: string) => console.log("Join game clicked", id)}
      />
    ))}
  </div>
);

const mockVariants: VariantForSelector[] = [
  {
    id: "classical",
    name: "Classical",
    author: "Allan B. Calhamer",
    nations: [
      { name: "Austria", color: "#FF0000" },
      { name: "England", color: "#0000FF" },
      { name: "France", color: "#00FFFF" },
      { name: "Germany", color: "#808080" },
      { name: "Italy", color: "#00FF00" },
      { name: "Russia", color: "#FFFFFF" },
      { name: "Turkey", color: "#FFFF00" },
    ],
    templatePhase: {
      id: 1,
      ordinal: 1,
      season: "Spring",
      year: 1901,
      name: "Spring 1901 Movement",
      type: "Movement",
      remainingTime: 0,
      scheduledResolution: "",
      status: "active",
      units: [],
      supplyCenters: [],
    },
  },
  {
    id: "hundred",
    name: "Hundred Years War",
    author: "Andy Schwarz",
    nations: [
      { name: "England", color: "#0000FF" },
      { name: "France", color: "#00FFFF" },
    ],
    templatePhase: {
      id: 2,
      ordinal: 1,
      season: "Spring",
      year: 1337,
      name: "Spring 1337 Movement",
      type: "Movement",
      remainingTime: 0,
      scheduledResolution: "",
      status: "active",
      units: [],
      supplyCenters: [],
    },
  },
];

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

export const CreateGameStandard: Story = {
  args: {
    left: (
      <Navigation
        items={createNavItems("/create-game")}
        variant="sidebar"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
    center: (
      <CreateGame
        currentTab="standard"
        onTabChange={action("tab-changed")}
        onStandardGameSubmit={async data => {
          action("standard-game-submitted")(data);
          console.log("Standard game:", data);
        }}
        onSandboxGameSubmit={async data => {
          action("sandbox-game-submitted")(data);
          console.log("Sandbox game:", data);
        }}
        isStandardGameSubmitting={false}
        isSandboxGameSubmitting={false}
        variants={mockVariants}
        isLoadingVariants={false}
      />
    ),
    right: <InfoPanel />,
    bottom: (
      <Navigation
        items={createNavItems("/create-game")}
        variant="bottom"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
  },
};

export const CreateGameSandbox: Story = {
  args: {
    left: (
      <Navigation
        items={createNavItems("/create-game")}
        variant="sidebar"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
    center: (
      <CreateGame
        currentTab="sandbox"
        onTabChange={action("tab-changed")}
        onStandardGameSubmit={async data => {
          action("standard-game-submitted")(data);
          console.log("Standard game:", data);
        }}
        onSandboxGameSubmit={async data => {
          action("sandbox-game-submitted")(data);
          console.log("Sandbox game:", data);
        }}
        isStandardGameSubmitting={false}
        isSandboxGameSubmitting={false}
        variants={mockVariants}
        isLoadingVariants={false}
      />
    ),
    right: <InfoPanel />,
    bottom: (
      <Navigation
        items={createNavItems("/create-game")}
        variant="bottom"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
  },
};

export const CreateGameLoading: Story = {
  args: {
    left: (
      <Navigation
        items={createNavItems("/create-game")}
        variant="sidebar"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
    center: (
      <CreateGame
        currentTab="standard"
        onTabChange={action("tab-changed")}
        onStandardGameSubmit={async data => {
          action("standard-game-submitted")(data);
        }}
        onSandboxGameSubmit={async data => {
          action("sandbox-game-submitted")(data);
        }}
        isStandardGameSubmitting={false}
        isSandboxGameSubmitting={false}
        variants={undefined}
        isLoadingVariants={true}
      />
    ),
    right: <InfoPanel />,
    bottom: (
      <Navigation
        items={createNavItems("/create-game")}
        variant="bottom"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
  },
};

export const CreateGameSubmitting: Story = {
  args: {
    left: (
      <Navigation
        items={createNavItems("/create-game")}
        variant="sidebar"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
    center: (
      <CreateGame
        currentTab="standard"
        onTabChange={action("tab-changed")}
        onStandardGameSubmit={async data => {
          action("standard-game-submitted")(data);
        }}
        onSandboxGameSubmit={async data => {
          action("sandbox-game-submitted")(data);
        }}
        isStandardGameSubmitting={true}
        isSandboxGameSubmitting={false}
        variants={mockVariants}
        isLoadingVariants={false}
      />
    ),
    right: <InfoPanel />,
    bottom: (
      <Navigation
        items={createNavItems("/create-game")}
        variant="bottom"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
  },
};

export const MyGamesActive: Story = {
  args: {
    left: (
      <Navigation
        items={createNavItems("/")}
        variant="sidebar"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
    center: (
      <MyGames
        selectedStatus="active"
        onStatusChange={action("status-changed")}
        isLoading={false}
        games={mockMyGames}
        onClickGame={action("game-clicked")}
        onClickGameInfo={action("game-info-clicked")}
        onClickPlayerInfo={action("player-info-clicked")}
        onClickJoinGame={action("join-game-clicked")}
      />
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

export const MyGamesPending: Story = {
  args: {
    left: (
      <Navigation
        items={createNavItems("/")}
        variant="sidebar"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
    center: (
      <MyGames
        selectedStatus="pending"
        onStatusChange={action("status-changed")}
        isLoading={false}
        games={mockMyGames}
        onClickGame={action("game-clicked")}
        onClickGameInfo={action("game-info-clicked")}
        onClickPlayerInfo={action("player-info-clicked")}
        onClickJoinGame={action("join-game-clicked")}
      />
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

export const MyGamesCompleted: Story = {
  args: {
    left: (
      <Navigation
        items={createNavItems("/")}
        variant="sidebar"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
    center: (
      <MyGames
        selectedStatus="completed"
        onStatusChange={action("status-changed")}
        isLoading={false}
        games={mockMyGames}
        onClickGame={action("game-clicked")}
        onClickGameInfo={action("game-info-clicked")}
        onClickPlayerInfo={action("player-info-clicked")}
        onClickJoinGame={action("join-game-clicked")}
      />
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

export const MyGamesLoading: Story = {
  args: {
    left: (
      <Navigation
        items={createNavItems("/")}
        variant="sidebar"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
    center: (
      <MyGames
        selectedStatus="active"
        onStatusChange={action("status-changed")}
        isLoading={true}
        games={undefined}
        onClickGame={action("game-clicked")}
        onClickGameInfo={action("game-info-clicked")}
        onClickPlayerInfo={action("player-info-clicked")}
        onClickJoinGame={action("join-game-clicked")}
      />
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

export const MyGamesEmpty: Story = {
  args: {
    left: (
      <Navigation
        items={createNavItems("/")}
        variant="sidebar"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
    center: (
      <MyGames
        selectedStatus="active"
        onStatusChange={action("status-changed")}
        isLoading={false}
        games={[]}
        onClickGame={action("game-clicked")}
        onClickGameInfo={action("game-info-clicked")}
        onClickPlayerInfo={action("player-info-clicked")}
        onClickJoinGame={action("join-game-clicked")}
      />
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

export const FindGamesDefault: Story = {
  args: {
    left: (
      <Navigation
        items={createNavItems("/find-games")}
        variant="sidebar"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
    center: (
      <FindGames
        isLoading={false}
        games={mockMyGames.filter(g => g.canJoin)}
        onClickGame={action("game-clicked")}
        onClickGameInfo={action("game-info-clicked")}
        onClickPlayerInfo={action("player-info-clicked")}
        onClickJoinGame={action("join-game-clicked")}
      />
    ),
    right: <InfoPanel />,
    bottom: (
      <Navigation
        items={createNavItems("/find-games")}
        variant="bottom"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
  },
};

export const FindGamesLoading: Story = {
  args: {
    left: (
      <Navigation
        items={createNavItems("/find-games")}
        variant="sidebar"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
    center: (
      <FindGames
        isLoading={true}
        games={undefined}
        onClickGame={action("game-clicked")}
        onClickGameInfo={action("game-info-clicked")}
        onClickPlayerInfo={action("player-info-clicked")}
        onClickJoinGame={action("join-game-clicked")}
      />
    ),
    right: <InfoPanel />,
    bottom: (
      <Navigation
        items={createNavItems("/find-games")}
        variant="bottom"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
  },
};

export const FindGamesEmpty: Story = {
  args: {
    left: (
      <Navigation
        items={createNavItems("/find-games")}
        variant="sidebar"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
    center: (
      <FindGames
        isLoading={false}
        games={[]}
        onClickGame={action("game-clicked")}
        onClickGameInfo={action("game-info-clicked")}
        onClickPlayerInfo={action("player-info-clicked")}
        onClickJoinGame={action("join-game-clicked")}
      />
    ),
    right: <InfoPanel />,
    bottom: (
      <Navigation
        items={createNavItems("/find-games")}
        variant="bottom"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
  },
};

export const SandboxGamesDefault: Story = {
  args: {
    left: (
      <Navigation
        items={createNavItems("/sandbox")}
        variant="sidebar"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
    center: (
      <SandboxGames
        isLoading={false}
        games={mockMyGames.filter(g => g.status === "active").slice(0, 2)}
        onClickGame={action("game-clicked")}
        onClickGameInfo={action("game-info-clicked")}
        onClickPlayerInfo={action("player-info-clicked")}
        onClickJoinGame={action("join-game-clicked")}
        onClickCreateSandbox={action("create-sandbox-clicked")}
      />
    ),
    right: <InfoPanel />,
    bottom: (
      <Navigation
        items={createNavItems("/sandbox")}
        variant="bottom"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
  },
};

export const SandboxGamesLoading: Story = {
  args: {
    left: (
      <Navigation
        items={createNavItems("/sandbox")}
        variant="sidebar"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
    center: (
      <SandboxGames
        isLoading={true}
        games={undefined}
        onClickGame={action("game-clicked")}
        onClickGameInfo={action("game-info-clicked")}
        onClickPlayerInfo={action("player-info-clicked")}
        onClickJoinGame={action("join-game-clicked")}
        onClickCreateSandbox={action("create-sandbox-clicked")}
      />
    ),
    right: <InfoPanel />,
    bottom: (
      <Navigation
        items={createNavItems("/sandbox")}
        variant="bottom"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
  },
};

export const SandboxGamesEmpty: Story = {
  args: {
    left: (
      <Navigation
        items={createNavItems("/sandbox")}
        variant="sidebar"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
    center: (
      <SandboxGames
        isLoading={false}
        games={[]}
        onClickGame={action("game-clicked")}
        onClickGameInfo={action("game-info-clicked")}
        onClickPlayerInfo={action("player-info-clicked")}
        onClickJoinGame={action("join-game-clicked")}
        onClickCreateSandbox={action("create-sandbox-clicked")}
      />
    ),
    right: <InfoPanel />,
    bottom: (
      <Navigation
        items={createNavItems("/sandbox")}
        variant="bottom"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
  },
};

export const ProfileDefault: Story = {
  args: {
    left: (
      <Navigation
        items={createNavItems("/profile")}
        variant="sidebar"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
    center: (
      <Profile
        isLoading={false}
        userProfile={{
          name: "John Smith",
          picture: null,
        }}
        onUpdateName={action("update-name")}
        isSubmitting={false}
        pushNotificationsEnabled={false}
        pushNotificationsPermissionDenied={false}
        pushNotificationsError={undefined}
        onTogglePushNotifications={action("toggle-push-notifications")}
        onLogout={action("logout")}
      />
    ),
    right: <InfoPanel />,
    bottom: (
      <Navigation
        items={createNavItems("/profile")}
        variant="bottom"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
  },
};

export const ProfileWithAvatar: Story = {
  args: {
    left: (
      <Navigation
        items={createNavItems("/profile")}
        variant="sidebar"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
    center: (
      <Profile
        isLoading={false}
        userProfile={{
          name: "Jane Doe",
          picture: "https://i.pravatar.cc/150?img=5",
        }}
        onUpdateName={action("update-name")}
        isSubmitting={false}
        pushNotificationsEnabled={true}
        pushNotificationsPermissionDenied={false}
        pushNotificationsError={undefined}
        onTogglePushNotifications={action("toggle-push-notifications")}
        onLogout={action("logout")}
      />
    ),
    right: <InfoPanel />,
    bottom: (
      <Navigation
        items={createNavItems("/profile")}
        variant="bottom"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
  },
};

export const ProfileEditingName: Story = {
  args: {
    left: (
      <Navigation
        items={createNavItems("/profile")}
        variant="sidebar"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
    center: (
      <Profile
        isLoading={false}
        userProfile={{
          name: "John Smith",
          picture: null,
        }}
        onUpdateName={action("update-name")}
        isSubmitting={false}
        pushNotificationsEnabled={false}
        pushNotificationsPermissionDenied={false}
        pushNotificationsError={undefined}
        onTogglePushNotifications={action("toggle-push-notifications")}
        onLogout={action("logout")}
      />
    ),
    right: <InfoPanel />,
    bottom: (
      <Navigation
        items={createNavItems("/profile")}
        variant="bottom"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
  },
};

export const ProfileLoading: Story = {
  args: {
    left: (
      <Navigation
        items={createNavItems("/profile")}
        variant="sidebar"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
    center: (
      <Profile
        isLoading={true}
        userProfile={undefined}
        onUpdateName={action("update-name")}
        isSubmitting={false}
        pushNotificationsEnabled={false}
        pushNotificationsPermissionDenied={false}
        pushNotificationsError={undefined}
        onTogglePushNotifications={action("toggle-push-notifications")}
        onLogout={action("logout")}
      />
    ),
    right: <InfoPanel />,
    bottom: (
      <Navigation
        items={createNavItems("/profile")}
        variant="bottom"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
  },
};

export const ProfileNotificationsError: Story = {
  args: {
    left: (
      <Navigation
        items={createNavItems("/profile")}
        variant="sidebar"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
    center: (
      <Profile
        isLoading={false}
        userProfile={{
          name: "John Smith",
          picture: null,
        }}
        onUpdateName={action("update-name")}
        isSubmitting={false}
        pushNotificationsEnabled={false}
        pushNotificationsPermissionDenied={false}
        pushNotificationsError="Failed to register service worker"
        onTogglePushNotifications={action("toggle-push-notifications")}
        onLogout={action("logout")}
      />
    ),
    right: <InfoPanel />,
    bottom: (
      <Navigation
        items={createNavItems("/profile")}
        variant="bottom"
        onItemClick={path => console.log("Navigate to:", path)}
      />
    ),
  },
};
