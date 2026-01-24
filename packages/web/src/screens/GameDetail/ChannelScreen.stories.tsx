import type { Meta, StoryObj } from "@storybook/react";
import { ChannelScreen } from "./ChannelScreen";
import {
  getGameRetrieveMockHandler,
  getVariantsListMockHandler,
  getGamesChannelsListMockHandler,
  getGamePhasesListMockHandler,
  getGamesChannelsMessagesCreateCreateMockHandler,
  GameRetrieve,
  Channel,
  PhaseList,
  ChannelMessage,
} from "@/api/generated/endpoints";
import { mockGames, mockVariants, mockNations } from "@/mocks";
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

const mockChannelWithMessages: Channel = {
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
    {
      id: 2,
      body: "Sounds good! I'll move to Burgundy.",
      sender: {
        id: 2,
        name: "Bob",
        picture: null,
        nation: mockNations[1],
        isCurrentUser: true,
      },
      createdAt: "2024-01-15T12:05:00Z",
    },
    {
      id: 3,
      body: "Perfect, I'll support you from Munich.",
      sender: {
        id: 1,
        name: "Alice",
        picture: null,
        nation: mockNations[0],
        isCurrentUser: false,
      },
      createdAt: "2024-01-15T12:10:00Z",
    },
    {
      id: 4,
      body: "Let me know if you need anything else.",
      sender: {
        id: 1,
        name: "Alice",
        picture: null,
        nation: mockNations[0],
        isCurrentUser: false,
      },
      createdAt: "2024-01-15T12:11:00Z",
    },
  ],
};

const mockChannelNoMessages: Channel = {
  id: 2,
  name: "New Private Chat",
  private: true,
  memberIds: [1, 3],
  messages: [],
};

const mockMessageResponse: ChannelMessage = {
  id: 5,
  body: "Test message",
  sender: {
    id: 2,
    name: "Bob",
    picture: null,
    nation: mockNations[1],
    isCurrentUser: true,
  },
  createdAt: new Date().toISOString(),
};

const meta = {
  title: "Screens/GameDetail/ChannelScreen",
  component: ChannelScreen,
  decorators: [withGameDetailLayout],
  parameters: {
    layout: "fullscreen",
    router: {
      path: "/game/:gameId/phase/:phaseId/chat/channel/:channelId",
    },
  },
} satisfies Meta<typeof ChannelScreen>;

export default meta;
type Story = StoryObj<typeof meta>;

export const WithMessages: Story = {
  parameters: {
    router: {
      initialEntries: ["/game/game-1/phase/1/chat/channel/1"],
    },
    msw: {
      handlers: [
        getGameRetrieveMockHandler(mockGames[0] as GameRetrieve),
        getVariantsListMockHandler(mockVariants),
        getGamesChannelsListMockHandler([mockChannelWithMessages]),
        getGamePhasesListMockHandler(mockPhasesList),
        getGamesChannelsMessagesCreateCreateMockHandler(mockMessageResponse),
      ],
    },
  },
};

export const NoMessages: Story = {
  parameters: {
    router: {
      initialEntries: ["/game/game-1/phase/1/chat/channel/2"],
    },
    msw: {
      handlers: [
        getGameRetrieveMockHandler(mockGames[0] as GameRetrieve),
        getVariantsListMockHandler(mockVariants),
        getGamesChannelsListMockHandler([mockChannelNoMessages]),
        getGamePhasesListMockHandler(mockPhasesList),
        getGamesChannelsMessagesCreateCreateMockHandler(mockMessageResponse),
      ],
    },
  },
};
