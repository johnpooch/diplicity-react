import type {
  Channel,
  ChannelMessage,
  GameList,
  GameListCurrentPhase,
  Member,
  Order,
  OrderTypeEnum,
  PhaseRetrieve,
  PhaseState,
  Province,
  StatusEnum,
  SupplyCenter,
  Unit,
  UnitTypeEnum,
} from "@/api/generated/endpoints";
import type { GameFixture } from "./types";
import {
  classicalStartSupplyCenters,
  classicalStartUnits,
  nation,
  province,
} from "./classical";

const HOUR = 60 * 60;

export const futureIso = (seconds: number) =>
  new Date(Date.now() + seconds * 1000).toISOString();

interface PhaseOverrides {
  season?: string;
  year?: number;
  type?: string;
  status?: StatusEnum;
  remainingTime?: number;
  units?: Unit[];
  supplyCenters?: SupplyCenter[];
  previousPhaseId?: number | null;
  nextPhaseId?: number | null;
}

export const makePhase = (
  id: number,
  ordinal: number,
  overrides: PhaseOverrides = {}
): PhaseRetrieve => {
  const season = overrides.season ?? "Spring";
  const year = overrides.year ?? 1901;
  const type = overrides.type ?? "Movement";
  const remainingTime = overrides.remainingTime ?? 24 * HOUR;
  return {
    id,
    ordinal,
    season,
    year,
    name: `${season} ${year}, ${type}`,
    type,
    remainingTime,
    scheduledResolution: futureIso(remainingTime),
    status: overrides.status ?? "active",
    units: overrides.units ?? classicalStartUnits,
    supplyCenters: overrides.supplyCenters ?? classicalStartSupplyCenters,
    previousPhaseId: overrides.previousPhaseId ?? null,
    nextPhaseId: overrides.nextPhaseId ?? null,
    provinceNations: "",
  };
};

export const toCurrentPhase = (phase: PhaseRetrieve): GameListCurrentPhase => ({
  id: phase.id,
  ordinal: phase.ordinal,
  season: phase.season,
  year: phase.year,
  name: phase.name,
  type: phase.type,
  status: phase.status,
  scheduledResolution: phase.scheduledResolution,
  remainingTime: phase.remainingTime,
});

type GameOverrides = Partial<Omit<GameList, "id" | "name">>;

export const makeGame = (
  id: string,
  name: string,
  members: Member[],
  phases: PhaseRetrieve[],
  overrides: GameOverrides = {}
): GameList => {
  const currentPhase =
    phases.find(p => p.status === "active") ??
    [...phases].reverse().find(p => p.status === "completed") ??
    null;
  return {
    id,
    name,
    status: "active",
    createdAt: "2026-05-01T10:00:00Z",
    canJoin: false,
    canLeave: false,
    canDelete: false,
    canManage: false,
    gameMaster: null,
    variantId: "classical",
    phases: phases.map(p => p.id),
    currentPhaseId: currentPhase?.id ?? null,
    currentPhase: currentPhase ? toCurrentPhase(currentPhase) : null,
    phaseConfirmed: false,
    private: false,
    anonymous: false,
    movementPhaseDuration: "24 hours",
    retreatPhaseDuration: null,
    nationAssignment: "random",
    members,
    victory: null,
    sandbox: false,
    isPaused: false,
    pausedAt: null,
    nmrExtensionsAllowed: 2,
    deadlineMode: "duration",
    fixedDeadlineTime: null,
    fixedDeadlineTimezone: null,
    movementFrequency: null,
    retreatFrequency: null,
    pressType: "full_press",
    minReliability: "open",
    totalUnreadMessageCount: 0,
    ...overrides,
  };
};

export const makeUnit = (
  type: UnitTypeEnum,
  nationId: string,
  provinceId: string,
  overrides: Partial<Unit> = {}
): Unit => ({
  type,
  nation: nation(nationId),
  province: province(provinceId),
  dislodged: false,
  dislodgedBy: null,
  ...overrides,
});

export const makeSupplyCenter = (
  nationId: string,
  provinceId: string
): SupplyCenter => ({
  nation: nation(nationId),
  province: province(provinceId),
});

interface OrderSpec {
  nationId: string;
  unitType: UnitTypeEnum;
  orderType: OrderTypeEnum;
  source: string;
  target?: string;
  aux?: string;
  succeeded?: boolean;
  failedBy?: string;
}

const orderTitle = (spec: OrderSpec, source: Province): string => {
  const unit = spec.unitType === "Army" ? "A" : "F";
  switch (spec.orderType) {
    case "Hold":
      return `${unit} ${source.name} Hold`;
    case "Move":
    case "MoveViaConvoy":
      return `${unit} ${source.name} - ${province(spec.target!).name}`;
    case "Support":
      return spec.target && spec.target !== spec.aux
        ? `${unit} ${source.name} S ${province(spec.aux!).name} - ${province(spec.target).name}`
        : `${unit} ${source.name} S ${province(spec.aux!).name}`;
    case "Convoy":
      return `${unit} ${source.name} C ${province(spec.aux!).name} - ${province(spec.target!).name}`;
    case "Build":
      return `Build ${spec.unitType} ${source.name}`;
    case "Disband":
      return `Disband ${unit} ${source.name}`;
  }
};

export const makeOrder = (spec: OrderSpec): Order => {
  const source = province(spec.source);
  const target = spec.target ? province(spec.target) : null;
  const aux = spec.aux ? province(spec.aux) : null;
  const title = orderTitle(spec, source);
  return {
    source,
    sourceCoast: null,
    // The generated Order type marks target/aux/namedCoast as non-nullable,
    // but the real API returns null for orders where they do not apply.
    target: target as Order["target"],
    aux: aux as Order["aux"],
    namedCoast: null as unknown as Order["namedCoast"],
    resolution:
      spec.succeeded === false
        ? {
            status: "Failed",
            by: spec.failedBy ? province(spec.failedBy) : null,
          }
        : { status: "Succeeded", by: null },
    options: [],
    orderType: spec.orderType,
    unitType: spec.unitType,
    nation: nation(spec.nationId),
    complete: true,
    step: "completed",
    title,
    summary: title,
  };
};

let phaseStateIdCounter = 0;

export const makePhaseState = (
  member: Member,
  orderableProvinceIds: string[],
  overrides: Partial<Omit<PhaseState, "member" | "orderableProvinces">> = {}
): PhaseState => ({
  id: `ps-${++phaseStateIdCounter}`,
  ordersConfirmed: false,
  eliminated: false,
  orderableProvinces: orderableProvinceIds.map(province),
  member,
  ...overrides,
});

let channelIdCounter = 0;
let messageIdCounter = 0;

export const makeMessage = (
  sender: Member,
  body: string,
  createdAt: string
): ChannelMessage => ({
  id: ++messageIdCounter,
  body,
  sender: {
    id: sender.id,
    userId: sender.userId,
    name: sender.name,
    picture: sender.picture,
    isCurrentUser: sender.isCurrentUser,
    nation: nation((sender.nation ?? "england").toLowerCase()),
  },
  createdAt,
});

export const makeChannel = (
  name: string,
  members: Member[],
  messages: ChannelMessage[],
  overrides: Partial<Channel> = {}
): Channel => ({
  id: ++channelIdCounter,
  name,
  private: name !== "Public Press",
  messages,
  unreadMessageCount: 0,
  memberIds: members.map(m => m.id),
  ...overrides,
});

export const makeFixture = (
  fixture: Partial<GameFixture> & Pick<GameFixture, "description" | "game">
): GameFixture => ({
  phases: [],
  ordersByPhase: {},
  phaseStates: [],
  channels: [],
  drawProposals: [],
  options: { orders: [], fieldOrder: {} },
  totalUnreadMessageCount: 0,
  ...fixture,
});
