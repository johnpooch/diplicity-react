import type { Meta, StoryObj } from "@storybook/react";
import { OrdersScreen } from "./OrdersScreen";
import {
  getGameRetrieveMockHandler,
  getVariantsListMockHandler,
  getGameOrdersListMockHandler,
  getGamePhaseRetrieveMockHandler,
  getGamePhaseStatesListMockHandler,
  getGamePhasesListMockHandler,
  getGameConfirmPhasePartialUpdateMockHandler,
  getGameOrdersDeleteDestroyMockHandler,
  getGameResolvePhaseCreateMockHandler,
  GameRetrieve,
  PhaseList,
} from "@/api/generated/endpoints";
import {
  mockGames,
  mockVariants,
  mockPhaseMovement,
  mockOrders,
  mockPhaseStates,
  mockPhaseStatesNoOrders,
  mockSandboxGames,
  mockMembers,
} from "@/mocks";
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
  {
    id: 2,
    ordinal: 2,
    name: "Fall 1901 Movement",
    season: "Fall",
    year: 1901,
    type: "Movement",
    status: "active",
  },
];

// For active phase (non-sandbox), only the current user's nation has orderable provinces
const mockPhaseStatesSingleNation = mockPhaseStates.map(ps =>
  ps.member.isCurrentUser
    ? ps
    : { ...ps, orderableProvinces: [] }
);

// Only include the current user's order for single-nation active phase
// Active phase orders have no resolution yet (empty status)
const mockOrdersSingleNation = mockOrders
  .filter(order => order.nation.name === mockMembers[6].nation)
  .map(order => ({ ...order, resolution: { status: "", by: null } }));

// Active phase orders for sandbox (all nations, no resolutions)
const mockOrdersActivePhase = mockOrders.map(order => ({
  ...order,
  resolution: { status: "", by: null },
}));

const mockCompletedPhase = {
  ...mockPhaseMovement,
  status: "completed" as const,
};

const meta = {
  title: "Screens/GameDetail/OrdersScreen",
  component: OrdersScreen,
  decorators: [withGameDetailLayout],
  parameters: {
    layout: "fullscreen",
    router: {
      path: "/game/:gameId/phase/:phaseId/orders",
    },
  },
} satisfies Meta<typeof OrdersScreen>;

export default meta;
type Story = StoryObj<typeof meta>;

export const ActivePhaseWithOrders: Story = {
  parameters: {
    router: {
      initialEntries: ["/game/game-1/phase/1/orders"],
    },
    msw: {
      handlers: [
        getGameRetrieveMockHandler(mockGames[0] as GameRetrieve),
        getVariantsListMockHandler(mockVariants),
        getGamePhaseRetrieveMockHandler(mockPhaseMovement),
        getGameOrdersListMockHandler(mockOrdersSingleNation),
        getGamePhaseStatesListMockHandler(mockPhaseStatesSingleNation),
        getGamePhasesListMockHandler(mockPhasesList),
        getGameConfirmPhasePartialUpdateMockHandler(),
        getGameOrdersDeleteDestroyMockHandler(),
      ],
    },
  },
};

export const ActivePhaseNoOrdersRequired: Story = {
  parameters: {
    router: {
      initialEntries: ["/game/game-1/phase/1/orders"],
    },
    msw: {
      handlers: [
        getGameRetrieveMockHandler(mockGames[0] as GameRetrieve),
        getVariantsListMockHandler(mockVariants),
        getGamePhaseRetrieveMockHandler(mockPhaseMovement),
        getGameOrdersListMockHandler([]),
        getGamePhaseStatesListMockHandler(mockPhaseStatesNoOrders),
        getGamePhasesListMockHandler(mockPhasesList),
        getGameConfirmPhasePartialUpdateMockHandler(),
      ],
    },
  },
};

export const InactivePhaseWithOrders: Story = {
  parameters: {
    router: {
      initialEntries: ["/game/game-1/phase/1/orders"],
    },
    msw: {
      handlers: [
        getGameRetrieveMockHandler(mockGames[0] as GameRetrieve),
        getVariantsListMockHandler(mockVariants),
        getGamePhaseRetrieveMockHandler(mockCompletedPhase),
        getGameOrdersListMockHandler(mockOrders),
        getGamePhaseStatesListMockHandler(mockPhaseStates),
        getGamePhasesListMockHandler(mockPhasesList),
      ],
    },
  },
};

export const InactivePhaseNoOrders: Story = {
  parameters: {
    router: {
      initialEntries: ["/game/game-1/phase/1/orders"],
    },
    msw: {
      handlers: [
        getGameRetrieveMockHandler(mockGames[0] as GameRetrieve),
        getVariantsListMockHandler(mockVariants),
        getGamePhaseRetrieveMockHandler(mockCompletedPhase),
        getGameOrdersListMockHandler([]),
        getGamePhaseStatesListMockHandler(mockPhaseStates),
        getGamePhasesListMockHandler(mockPhasesList),
      ],
    },
  },
};

export const SandboxGame: Story = {
  parameters: {
    router: {
      initialEntries: ["/game/sandbox-1/phase/1/orders"],
    },
    msw: {
      handlers: [
        getGameRetrieveMockHandler(mockSandboxGames[0] as GameRetrieve),
        getVariantsListMockHandler(mockVariants),
        getGamePhaseRetrieveMockHandler(mockPhaseMovement),
        getGameOrdersListMockHandler(mockOrdersActivePhase),
        getGamePhaseStatesListMockHandler(mockPhaseStates),
        getGamePhasesListMockHandler(mockPhasesList),
        getGameResolvePhaseCreateMockHandler(),
        getGameOrdersDeleteDestroyMockHandler(),
      ],
    },
  },
};
