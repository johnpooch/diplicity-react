import type { Meta, StoryObj } from "@storybook/react";
import { ChannelListScreen } from "./ChannelListScreen";
import {
  getGameRetrieveMockHandler,
  getVariantsListMockHandler,
  getGamesChannelsListMockHandler,
  getGamePhasesListMockHandler,
  GameRetrieve,
  Channel,
  PhaseList,
} from "@/api/generated/endpoints";
import { mockGames, mockVariants, mockNations, mockSandboxGames } from "@/mocks";
import { withGameDetailLayout } from "@/stories/decorators";

const mockPhasesList: PhaseList[] = [
  {
    id: 1,
    ordinal: 1,
    name: "Spring 1901 Movement",
    season: "Spring",
    year: 1901,
    type: "Movement",
    status: "active",
  },
];

const mockChannels: Channel[] = [
  {
    id: 1,
    name: "Austria-England Alliance",
    private: true,
    memberIds: [1, 2],
    messages: [
      {
        id: 1,
        body: "Let's coordinate our moves against France",
        sender: {
          id: 1,
          name: "Alice",
          picture: null,
          nation: mockNations[0],
          isCurrentUser: false,
        },
        createdAt: "2024-01-15T12:00:00Z",
      },
    ],
  },
  {
    id: 2,
    name: "Public Chat",
    private: false,
    memberIds: [1, 2, 3, 4, 5, 6, 7],
    messages: [
      {
        id: 2,
        body: "Good luck everyone!",
        sender: {
          id: 3,
          name: "Charlie",
          picture: null,
          nation: mockNations[2],
          isCurrentUser: false,
        },
        createdAt: "2024-01-15T11:00:00Z",
      },
    ],
  },
  {
    id: 3,
    name: "Italy-Turkey Pact",
    private: true,
    memberIds: [5, 7],
    messages: [],
  },
];

const meta = {
  title: "Screens/GameDetail/ChannelListScreen",
  component: ChannelListScreen,
  decorators: [withGameDetailLayout],
  parameters: {
    layout: "fullscreen",
    router: {
      path: "/game/:gameId/phase/:phaseId/chat",
    },
  },
} satisfies Meta<typeof ChannelListScreen>;

export default meta;
type Story = StoryObj<typeof meta>;

export const WithChannels: Story = {
  parameters: {
    router: {
      initialEntries: ["/game/game-1/phase/1/chat"],
    },
    msw: {
      handlers: [
        getGameRetrieveMockHandler(mockGames[0] as GameRetrieve),
        getVariantsListMockHandler(mockVariants),
        getGamesChannelsListMockHandler(mockChannels),
        getGamePhasesListMockHandler(mockPhasesList),
      ],
    },
  },
};

export const NoChannels: Story = {
  parameters: {
    router: {
      initialEntries: ["/game/game-1/phase/1/chat"],
    },
    msw: {
      handlers: [
        getGameRetrieveMockHandler(mockGames[0] as GameRetrieve),
        getVariantsListMockHandler(mockVariants),
        getGamesChannelsListMockHandler([]),
        getGamePhasesListMockHandler(mockPhasesList),
      ],
    },
  },
};

export const SandboxGame: Story = {
  parameters: {
    router: {
      initialEntries: ["/game/sandbox-1/phase/1/chat"],
    },
    msw: {
      handlers: [
        getGameRetrieveMockHandler(mockSandboxGames[0] as GameRetrieve),
        getVariantsListMockHandler(mockVariants),
        getGamesChannelsListMockHandler([]),
        getGamePhasesListMockHandler(mockPhasesList),
      ],
    },
  },
};
