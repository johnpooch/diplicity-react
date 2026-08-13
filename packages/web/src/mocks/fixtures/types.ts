import type {
  ChannelMessage,
  DrawProposal,
  GameList,
  Order,
  OrderOptionsResponse,
  PhaseRetrieve,
  PhaseState,
} from "@/api/generated/endpoints";

export interface ChannelFixture {
  id: number;
  name: string;
  private: boolean;
  messages: ChannelMessage[];
  unreadMessageCount?: number;
}

export interface GameFixture {
  description: string;
  game: GameList;
  phases: PhaseRetrieve[];
  ordersByPhase: Record<number, Order[]>;
  phaseStates: PhaseState[];
  channels: ChannelFixture[];
  drawProposals: DrawProposal[];
  options: OrderOptionsResponse;
}
