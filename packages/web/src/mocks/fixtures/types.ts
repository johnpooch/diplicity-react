import type {
  Channel,
  DrawProposal,
  GameList,
  Order,
  OrderOptionsResponse,
  PhaseRetrieve,
  PhaseState,
} from "@/api/generated/endpoints";

export interface GameFixture {
  description: string;
  game: GameList;
  phases: PhaseRetrieve[];
  ordersByPhase: Record<number, Order[]>;
  phaseStates: PhaseState[];
  channels: Channel[];
  drawProposals: DrawProposal[];
  options: OrderOptionsResponse;
  totalUnreadMessageCount: number;
}
