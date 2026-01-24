import type { Meta, StoryObj } from "@storybook/react";
import { PhaseGuidance } from "./PhaseGuidance";
import {
  getGameRetrieveMockHandler,
  getGameOrdersListMockHandler,
  getGamePhaseRetrieveMockHandler,
  getGamePhaseStatesListMockHandler,
  GameRetrieve,
  PhaseRetrieve,
  PhaseState,
  StatusEnum,
} from "@/api/generated/endpoints";
import {
  mockGames,
  mockPhaseMovement,
  mockPhaseAdjustment,
  mockPhaseRetreat,
  mockOrders,
  mockPhaseStates,
  mockMembers,
  mockNations,
  mockProvinces,
} from "@/mocks";
import { Suspense } from "react";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";

const meta = {
  title: "Components/PhaseGuidance",
  component: PhaseGuidance,
  parameters: {
    layout: "centered",
    router: {
      initialEntries: ["/game/game-1/phase/1/orders"],
      path: "/game/:gameId/phase/:phaseId/orders",
    },
  },
  decorators: [
    Story => (
      <QueryErrorBoundary>
        <Suspense fallback={<div>Loading...</div>}>
          <div className="p-4">
            <Story />
          </div>
        </Suspense>
      </QueryErrorBoundary>
    ),
  ],
} satisfies Meta<typeof PhaseGuidance>;

export default meta;
type Story = StoryObj<typeof meta>;

// Current user is Turkey (index 6)
const currentUserPhaseState: PhaseState = {
  id: "ps-7",
  ordersConfirmed: false,
  eliminated: false,
  orderableProvinces: [mockProvinces[6]], // Constantinople
  member: mockMembers[6], // Turkey (current user)
};

// Phase state with multiple orderable provinces for current user
const multipleOrdersPhaseState: PhaseState = {
  id: "ps-7",
  ordersConfirmed: false,
  eliminated: false,
  orderableProvinces: [mockProvinces[5], mockProvinces[6]], // 2 provinces
  member: mockMembers[6], // Turkey (current user)
};

// Phase states for scenarios
const phaseStatesWithOrders = mockPhaseStates.map(ps =>
  ps.member.isCurrentUser ? currentUserPhaseState : { ...ps, orderableProvinces: [] }
);

const phaseStatesMultipleOrders = mockPhaseStates.map(ps =>
  ps.member.isCurrentUser ? multipleOrdersPhaseState : { ...ps, orderableProvinces: [] }
);

const phaseStatesNoOrders = mockPhaseStates.map(ps => ({
  ...ps,
  orderableProvinces: [],
}));

// Current user's order (Turkey)
const currentUserOrder = mockOrders.find(o => o.nation.name === "Turkey")!;

// Completed phase for historical view
const completedPhase: PhaseRetrieve = {
  ...mockPhaseMovement,
  status: "completed" as StatusEnum,
};

// Game with confirmed orders
const gameConfirmed: GameRetrieve = {
  ...(mockGames[0] as GameRetrieve),
  phaseConfirmed: true,
};

// Game with unconfirmed orders
const gameNotConfirmed: GameRetrieve = {
  ...(mockGames[0] as GameRetrieve),
  phaseConfirmed: false,
};

// Adjustment phase with builds needed (more SCs than units for Turkey)
const adjustmentPhaseBuildsNeeded: PhaseRetrieve = {
  ...mockPhaseAdjustment,
  supplyCenters: [
    ...mockPhaseAdjustment.supplyCenters,
    { province: mockProvinces[0], nation: mockNations[6] }, // Extra SC for Turkey
    { province: mockProvinces[1], nation: mockNations[6] }, // Another extra SC
  ],
};

// Adjustment phase with disbands needed (more units than SCs for Turkey)
const adjustmentPhaseDisbands: PhaseRetrieve = {
  ...mockPhaseAdjustment,
  units: [
    ...mockPhaseAdjustment.units,
    {
      type: "Army",
      nation: mockNations[6],
      province: mockProvinces[0],
      dislodged: false,
      dislodgedBy: null,
    },
    {
      type: "Army",
      nation: mockNations[6],
      province: mockProvinces[1],
      dislodged: false,
      dislodgedBy: null,
    },
  ],
  supplyCenters: mockPhaseAdjustment.supplyCenters.filter(
    sc => sc.nation.name !== "Turkey"
  ),
};

// Retreat phase with dislodged unit for Turkey
const retreatPhaseWithDislodged: PhaseRetrieve = {
  ...mockPhaseRetreat,
  units: [
    {
      type: "Fleet",
      nation: mockNations[6], // Turkey
      province: mockProvinces[6],
      dislodged: true,
      dislodgedBy: null,
    },
  ],
};

// Retreat phase with no dislodged units for Turkey
const retreatPhaseNoDislodged: PhaseRetrieve = {
  ...mockPhaseRetreat,
  units: [
    {
      type: "Army",
      nation: mockNations[0], // Austria (not current user)
      province: mockProvinces[0],
      dislodged: true,
      dislodgedBy: null,
    },
  ],
};

export const MovementNoOrders: Story = {
  name: "Movement - No orders submitted (not confirmed)",
  parameters: {
    msw: {
      handlers: [
        getGameRetrieveMockHandler(gameNotConfirmed),
        getGamePhaseRetrieveMockHandler(mockPhaseMovement),
        getGameOrdersListMockHandler([]),
        getGamePhaseStatesListMockHandler(phaseStatesWithOrders),
      ],
    },
  },
};

export const MovementPartialOrders: Story = {
  name: "Movement - Partial orders (not confirmed)",
  parameters: {
    msw: {
      handlers: [
        getGameRetrieveMockHandler(gameNotConfirmed),
        getGamePhaseRetrieveMockHandler(mockPhaseMovement),
        getGameOrdersListMockHandler([currentUserOrder]),
        getGamePhaseStatesListMockHandler(phaseStatesMultipleOrders),
      ],
    },
  },
};

export const MovementAllOrdersNotConfirmed: Story = {
  name: "Movement - All orders submitted (not confirmed)",
  parameters: {
    msw: {
      handlers: [
        getGameRetrieveMockHandler(gameNotConfirmed),
        getGamePhaseRetrieveMockHandler(mockPhaseMovement),
        getGameOrdersListMockHandler([currentUserOrder]),
        getGamePhaseStatesListMockHandler(phaseStatesWithOrders),
      ],
    },
  },
};

export const MovementAllOrdersConfirmed: Story = {
  name: "Movement - All orders submitted (confirmed)",
  parameters: {
    msw: {
      handlers: [
        getGameRetrieveMockHandler(gameConfirmed),
        getGamePhaseRetrieveMockHandler(mockPhaseMovement),
        getGameOrdersListMockHandler([currentUserOrder]),
        getGamePhaseStatesListMockHandler(phaseStatesWithOrders),
      ],
    },
  },
};

export const MovementNoOrdersRequired: Story = {
  name: "Movement - No orders required",
  parameters: {
    msw: {
      handlers: [
        getGameRetrieveMockHandler(gameNotConfirmed),
        getGamePhaseRetrieveMockHandler(mockPhaseMovement),
        getGameOrdersListMockHandler([]),
        getGamePhaseStatesListMockHandler(phaseStatesNoOrders),
      ],
    },
  },
};

export const AdjustmentBuildsNeeded: Story = {
  name: "Adjustment - Builds needed (not confirmed)",
  parameters: {
    msw: {
      handlers: [
        getGameRetrieveMockHandler(gameNotConfirmed),
        getGamePhaseRetrieveMockHandler(adjustmentPhaseBuildsNeeded),
        getGameOrdersListMockHandler([]),
        getGamePhaseStatesListMockHandler(phaseStatesWithOrders),
      ],
    },
  },
};

export const AdjustmentDisbandsNeeded: Story = {
  name: "Adjustment - Disbands needed (not confirmed)",
  parameters: {
    msw: {
      handlers: [
        getGameRetrieveMockHandler(gameNotConfirmed),
        getGamePhaseRetrieveMockHandler(adjustmentPhaseDisbands),
        getGameOrdersListMockHandler([]),
        getGamePhaseStatesListMockHandler(phaseStatesWithOrders),
      ],
    },
  },
};

export const AdjustmentNoChanges: Story = {
  name: "Adjustment - No adjustments needed",
  parameters: {
    msw: {
      handlers: [
        getGameRetrieveMockHandler(gameNotConfirmed),
        getGamePhaseRetrieveMockHandler(mockPhaseAdjustment),
        getGameOrdersListMockHandler([]),
        getGamePhaseStatesListMockHandler(phaseStatesWithOrders),
      ],
    },
  },
};

export const RetreatRequired: Story = {
  name: "Retreat - Retreat required (not confirmed)",
  parameters: {
    msw: {
      handlers: [
        getGameRetrieveMockHandler(gameNotConfirmed),
        getGamePhaseRetrieveMockHandler(retreatPhaseWithDislodged),
        getGameOrdersListMockHandler([]),
        getGamePhaseStatesListMockHandler(phaseStatesWithOrders),
      ],
    },
  },
};

export const RetreatNotRequired: Story = {
  name: "Retreat - No retreat required",
  parameters: {
    msw: {
      handlers: [
        getGameRetrieveMockHandler(gameNotConfirmed),
        getGamePhaseRetrieveMockHandler(retreatPhaseNoDislodged),
        getGameOrdersListMockHandler([]),
        getGamePhaseStatesListMockHandler(phaseStatesWithOrders),
      ],
    },
  },
};

export const HistoricalPhase: Story = {
  name: "Historical phase - No guidance",
  parameters: {
    msw: {
      handlers: [
        getGameRetrieveMockHandler(gameNotConfirmed),
        getGamePhaseRetrieveMockHandler(completedPhase),
        getGameOrdersListMockHandler(mockOrders),
        getGamePhaseStatesListMockHandler(mockPhaseStates),
      ],
    },
  },
};
