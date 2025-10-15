import { api } from "./api";
const injectedRtkApi = api.injectEndpoints({
  endpoints: (build) => ({
    apiSchemaRetrieve: build.query<
      ApiSchemaRetrieveApiResponse,
      ApiSchemaRetrieveApiArg
    >({
      query: (queryArg) => ({
        url: `/api/schema/`,
        params: {
          format: queryArg.format,
          lang: queryArg.lang,
        },
      }),
    }),
    apiTokenRefreshCreate: build.mutation<
      ApiTokenRefreshCreateApiResponse,
      ApiTokenRefreshCreateApiArg
    >({
      query: (queryArg) => ({
        url: `/api/token/refresh/`,
        method: "POST",
        body: queryArg.tokenRefresh,
      }),
    }),
    authLoginCreate: build.mutation<
      AuthLoginCreateApiResponse,
      AuthLoginCreateApiArg
    >({
      query: (queryArg) => ({
        url: `/auth/login/`,
        method: "POST",
        body: queryArg.auth,
      }),
    }),
    devicesList: build.query<DevicesListApiResponse, DevicesListApiArg>({
      query: () => ({ url: `/devices/` }),
    }),
    devicesCreate: build.mutation<
      DevicesCreateApiResponse,
      DevicesCreateApiArg
    >({
      query: (queryArg) => ({
        url: `/devices/`,
        method: "POST",
        body: queryArg.fcmDevice,
      }),
    }),
    devicesUpdate: build.mutation<
      DevicesUpdateApiResponse,
      DevicesUpdateApiArg
    >({
      query: (queryArg) => ({
        url: `/devices/`,
        method: "PUT",
        body: queryArg.fcmDevice,
      }),
    }),
    gameCreate: build.mutation<GameCreateApiResponse, GameCreateApiArg>({
      query: (queryArg) => ({
        url: `/game/`,
        method: "POST",
        body: queryArg.game,
      }),
    }),
    gameRetrieve: build.query<GameRetrieveApiResponse, GameRetrieveApiArg>({
      query: (queryArg) => ({ url: `/game/${queryArg.gameId}/` }),
    }),
    gameConfirmPhaseUpdate: build.mutation<
      GameConfirmPhaseUpdateApiResponse,
      GameConfirmPhaseUpdateApiArg
    >({
      query: (queryArg) => ({
        url: `/game/${queryArg.gameId}/confirm-phase/`,
        method: "PUT",
        body: queryArg.phaseState,
      }),
    }),
    gameConfirmPhasePartialUpdate: build.mutation<
      GameConfirmPhasePartialUpdateApiResponse,
      GameConfirmPhasePartialUpdateApiArg
    >({
      query: (queryArg) => ({
        url: `/game/${queryArg.gameId}/confirm-phase/`,
        method: "PATCH",
        body: queryArg.patchedPhaseState,
      }),
    }),
    gameJoinCreate: build.mutation<
      GameJoinCreateApiResponse,
      GameJoinCreateApiArg
    >({
      query: (queryArg) => ({
        url: `/game/${queryArg.gameId}/join/`,
        method: "POST",
        body: queryArg.member,
      }),
    }),
    gameLeaveDestroy: build.mutation<
      GameLeaveDestroyApiResponse,
      GameLeaveDestroyApiArg
    >({
      query: (queryArg) => ({
        url: `/game/${queryArg.gameId}/leave/`,
        method: "DELETE",
      }),
    }),
    gameOrdersCreate: build.mutation<
      GameOrdersCreateApiResponse,
      GameOrdersCreateApiArg
    >({
      query: (queryArg) => ({
        url: `/game/${queryArg.gameId}/orders/`,
        method: "POST",
        body: queryArg.order,
      }),
    }),
    gameOrdersList: build.query<
      GameOrdersListApiResponse,
      GameOrdersListApiArg
    >({
      query: (queryArg) => ({
        url: `/game/${queryArg.gameId}/orders/${queryArg.phaseId}`,
      }),
    }),
    gameOrdersDeleteDestroy: build.mutation<
      GameOrdersDeleteDestroyApiResponse,
      GameOrdersDeleteDestroyApiArg
    >({
      query: (queryArg) => ({
        url: `/game/${queryArg.gameId}/orders/delete/${queryArg.sourceId}`,
        method: "DELETE",
      }),
    }),
    gamePhaseStateRetrieve: build.query<
      GamePhaseStateRetrieveApiResponse,
      GamePhaseStateRetrieveApiArg
    >({
      query: (queryArg) => ({ url: `/game/${queryArg.gameId}/phase-state/` }),
    }),
    gamesList: build.query<GamesListApiResponse, GamesListApiArg>({
      query: (queryArg) => ({
        url: `/games/`,
        params: {
          can_join: queryArg.canJoin,
          mine: queryArg.mine,
        },
      }),
    }),
    gamesChannelsList: build.query<
      GamesChannelsListApiResponse,
      GamesChannelsListApiArg
    >({
      query: (queryArg) => ({ url: `/games/${queryArg.gameId}/channels/` }),
    }),
    gamesChannelsMessagesCreateCreate: build.mutation<
      GamesChannelsMessagesCreateCreateApiResponse,
      GamesChannelsMessagesCreateCreateApiArg
    >({
      query: (queryArg) => ({
        url: `/games/${queryArg.gameId}/channels/${queryArg.channelId}/messages/create/`,
        method: "POST",
        body: queryArg.channelMessage,
      }),
    }),
    gamesChannelsCreateCreate: build.mutation<
      GamesChannelsCreateCreateApiResponse,
      GamesChannelsCreateCreateApiArg
    >({
      query: (queryArg) => ({
        url: `/games/${queryArg.gameId}/channels/create/`,
        method: "POST",
        body: queryArg.channel,
      }),
    }),
    phaseResolveCreate: build.mutation<
      PhaseResolveCreateApiResponse,
      PhaseResolveCreateApiArg
    >({
      query: (queryArg) => ({
        url: `/phase/resolve/`,
        method: "POST",
        body: queryArg.phaseResolveResponse,
      }),
    }),
    userRetrieve: build.query<UserRetrieveApiResponse, UserRetrieveApiArg>({
      query: () => ({ url: `/user/` }),
    }),
    variantsList: build.query<VariantsListApiResponse, VariantsListApiArg>({
      query: () => ({ url: `/variants/` }),
    }),
    versionRetrieve: build.query<
      VersionRetrieveApiResponse,
      VersionRetrieveApiArg
    >({
      query: () => ({ url: `/version/` }),
    }),
  }),
  overrideExisting: false,
});
export { injectedRtkApi as service };
export type ApiSchemaRetrieveApiResponse = /** status 200  */ {
  [key: string]: any;
};
export type ApiSchemaRetrieveApiArg = {
  format?: "json" | "yaml";
  lang?:
    | "af"
    | "ar"
    | "ar-dz"
    | "ast"
    | "az"
    | "be"
    | "bg"
    | "bn"
    | "br"
    | "bs"
    | "ca"
    | "ckb"
    | "cs"
    | "cy"
    | "da"
    | "de"
    | "dsb"
    | "el"
    | "en"
    | "en-au"
    | "en-gb"
    | "eo"
    | "es"
    | "es-ar"
    | "es-co"
    | "es-mx"
    | "es-ni"
    | "es-ve"
    | "et"
    | "eu"
    | "fa"
    | "fi"
    | "fr"
    | "fy"
    | "ga"
    | "gd"
    | "gl"
    | "he"
    | "hi"
    | "hr"
    | "hsb"
    | "hu"
    | "hy"
    | "ia"
    | "id"
    | "ig"
    | "io"
    | "is"
    | "it"
    | "ja"
    | "ka"
    | "kab"
    | "kk"
    | "km"
    | "kn"
    | "ko"
    | "ky"
    | "lb"
    | "lt"
    | "lv"
    | "mk"
    | "ml"
    | "mn"
    | "mr"
    | "ms"
    | "my"
    | "nb"
    | "ne"
    | "nl"
    | "nn"
    | "os"
    | "pa"
    | "pl"
    | "pt"
    | "pt-br"
    | "ro"
    | "ru"
    | "sk"
    | "sl"
    | "sq"
    | "sr"
    | "sr-latn"
    | "sv"
    | "sw"
    | "ta"
    | "te"
    | "tg"
    | "th"
    | "tk"
    | "tr"
    | "tt"
    | "udm"
    | "uk"
    | "ur"
    | "uz"
    | "vi"
    | "zh-hans"
    | "zh-hant";
};
export type ApiTokenRefreshCreateApiResponse =
  /** status 200  */ TokenRefreshRead;
export type ApiTokenRefreshCreateApiArg = {
  tokenRefresh: TokenRefreshWrite;
};
export type AuthLoginCreateApiResponse = /** status 201  */ AuthRead;
export type AuthLoginCreateApiArg = {
  auth: AuthWrite;
};
export type DevicesListApiResponse = /** status 200  */ FcmDeviceRead[];
export type DevicesListApiArg = void;
export type DevicesCreateApiResponse = /** status 201  */ FcmDeviceRead;
export type DevicesCreateApiArg = {
  fcmDevice: FcmDevice;
};
export type DevicesUpdateApiResponse = /** status 200  */ FcmDeviceRead;
export type DevicesUpdateApiArg = {
  fcmDevice: FcmDevice;
};
export type GameCreateApiResponse = /** status 201  */ GameRead;
export type GameCreateApiArg = {
  game: GameWrite;
};
export type GameRetrieveApiResponse = /** status 200  */ GameRead;
export type GameRetrieveApiArg = {
  gameId: string;
};
export type GameConfirmPhaseUpdateApiResponse =
  /** status 200  */ PhaseStateRead;
export type GameConfirmPhaseUpdateApiArg = {
  gameId: string;
  phaseState: PhaseState;
};
export type GameConfirmPhasePartialUpdateApiResponse =
  /** status 200  */ PhaseStateRead;
export type GameConfirmPhasePartialUpdateApiArg = {
  gameId: string;
  patchedPhaseState: PatchedPhaseState;
};
export type GameJoinCreateApiResponse = /** status 201  */ MemberRead;
export type GameJoinCreateApiArg = {
  gameId: string;
  member: Member;
};
export type GameLeaveDestroyApiResponse = unknown;
export type GameLeaveDestroyApiArg = {
  gameId: string;
};
export type GameOrdersCreateApiResponse = /** status 201  */ OrderRead;
export type GameOrdersCreateApiArg = {
  gameId: string;
  order: Order;
};
export type GameOrdersListApiResponse = /** status 200  */ OrderRead[];
export type GameOrdersListApiArg = {
  gameId: string;
  phaseId: number;
};
export type GameOrdersDeleteDestroyApiResponse = unknown;
export type GameOrdersDeleteDestroyApiArg = {
  gameId: string;
  sourceId: string;
};
export type GamePhaseStateRetrieveApiResponse =
  /** status 200  */ PhaseStateRead;
export type GamePhaseStateRetrieveApiArg = {
  gameId: string;
};
export type GamesListApiResponse = /** status 200  */ GameRead[];
export type GamesListApiArg = {
  canJoin?: boolean;
  mine?: boolean;
};
export type GamesChannelsListApiResponse = /** status 200  */ ChannelRead[];
export type GamesChannelsListApiArg = {
  gameId: string;
};
export type GamesChannelsMessagesCreateCreateApiResponse =
  /** status 201  */ ChannelMessageRead;
export type GamesChannelsMessagesCreateCreateApiArg = {
  channelId: number;
  gameId: string;
  channelMessage: ChannelMessage;
};
export type GamesChannelsCreateCreateApiResponse =
  /** status 201  */ ChannelRead;
export type GamesChannelsCreateCreateApiArg = {
  gameId: string;
  channel: ChannelWrite;
};
export type PhaseResolveCreateApiResponse =
  /** status 200  */ PhaseResolveResponse;
export type PhaseResolveCreateApiArg = {
  phaseResolveResponse: PhaseResolveResponse;
};
export type UserRetrieveApiResponse = /** status 200  */ UserProfile;
export type UserRetrieveApiArg = void;
export type VariantsListApiResponse = /** status 200  */ VariantRead[];
export type VariantsListApiArg = void;
export type VersionRetrieveApiResponse = /** status 200  */ Version;
export type VersionRetrieveApiArg = void;
export type TokenRefresh = {};
export type TokenRefreshRead = {
  access: string;
};
export type TokenRefreshWrite = {
  refresh: string;
};
export type Auth = {};
export type AuthRead = {
  id: number;
  email: string;
  username: string;
  accessToken: string;
  refreshToken: string;
};
export type AuthWrite = {
  idToken: string;
};
export type TypeEnum = "ios" | "android" | "web";
export type FcmDevice = {
  name?: string | null;
  registrationId: string;
  /** Unique device identifier */
  deviceId?: string | null;
  /** Inactive devices will not be sent notifications */
  active?: boolean;
  type: TypeEnum;
};
export type FcmDeviceRead = {
  id: number;
  name?: string | null;
  registrationId: string;
  /** Unique device identifier */
  deviceId?: string | null;
  /** Inactive devices will not be sent notifications */
  active?: boolean;
  dateCreated: string | null;
  type: TypeEnum;
};
export type NationAssignmentEnum = "random" | "ordered";
export type MovementPhaseDurationEnum = "24 hours" | "48 hours" | "1 week";
export type Game = {
  name: string;
  nationAssignment: NationAssignmentEnum;
  movementPhaseDuration?: MovementPhaseDurationEnum;
  private: boolean;
};
export type StatusEnum = "pending" | "active" | "completed" | "template";
export type Nation = {
  name: string;
  color: string;
};
export type Province = {
  id: string;
  name: string;
  type: string;
  supplyCenter: boolean;
  parentId: string | null;
};
export type ProvinceRead = {
  id: string;
  name: string;
  type: string;
  supplyCenter: boolean;
  parentId: string | null;
  namedCoastIds: string[];
};
export type Unit = {
  type: string;
  nation: Nation;
  province: Province;
};
export type UnitRead = {
  type: string;
  nation: Nation;
  province: ProvinceRead;
  dislodgedBy: {
    [key: string]: any;
  } | null;
};
export type SupplyCenter = {
  province: Province;
  nation: Nation;
};
export type SupplyCenterRead = {
  province: ProvinceRead;
  nation: Nation;
};
export type Phase = {
  id: number;
  ordinal: number;
  season: string;
  year: number;
  name: string;
  type: string;
  remainingTime: number;
  scheduledResolution: string;
  status: StatusEnum;
  units: Unit[];
  supplyCenters: SupplyCenter[];
  options: any;
};
export type PhaseRead = {
  id: number;
  ordinal: number;
  season: string;
  year: number;
  name: string;
  type: string;
  remainingTime: number;
  scheduledResolution: string;
  status: StatusEnum;
  units: UnitRead[];
  supplyCenters: SupplyCenterRead[];
  options: any;
};
export type Variant = {
  id: string;
  name: string;
  description: string;
  author?: string;
  nations: Nation[];
  provinces: Province[];
  templatePhase: Phase;
};
export type VariantRead = {
  id: string;
  name: string;
  description: string;
  author?: string;
  nations: Nation[];
  provinces: ProvinceRead[];
  templatePhase: PhaseRead;
};
export type Member = {};
export type GameSummary = {
  name: string;
  status: string;
};
export type MemberRead = {
  id: number;
  username: string;
  name: string;
  picture: string;
  nation: string | null;
  isCurrentUser: boolean;
  game: GameSummary;
  supplyCenterCount: number;
};
export type GameRead = {
  id: string;
  status: string;
  canJoin: boolean;
  canLeave: boolean;
  phases: PhaseRead[];
  variant: VariantRead;
  members: MemberRead[];
  phaseConfirmed: boolean;
  name: string;
  nationAssignment: NationAssignmentEnum;
  movementPhaseDuration?: MovementPhaseDurationEnum;
  private: boolean;
};
export type GameWrite = {
  name: string;
  variantId: string;
  nationAssignment: NationAssignmentEnum;
  movementPhaseDuration?: MovementPhaseDurationEnum;
  private: boolean;
};
export type PhaseState = {};
export type PhaseStateRead = {
  id: string;
  ordersConfirmed: boolean;
  eliminated: boolean;
  orderableProvinces: ProvinceRead[];
};
export type PatchedPhaseState = {};
export type PatchedPhaseStateRead = {
  id?: string;
  ordersConfirmed?: boolean;
  eliminated?: boolean;
  orderableProvinces?: ProvinceRead[];
};
export type Order = {
  selected?: string[];
};
export type OrderResolution = {
  status: string;
  by: Province | null;
};
export type OrderResolutionRead = {
  status: string;
  by: ProvinceRead | null;
};
export type OrderOption = {
  value: string;
  label: string;
};
export type OrderTypeEnum =
  | "Move"
  | "MoveViaConvoy"
  | "Hold"
  | "Support"
  | "Convoy"
  | "Build"
  | "Disband";
export type UnitTypeEnum = "Army" | "Fleet";
export type StepEnum =
  | "select-order-type"
  | "select-unit-type"
  | "select-target"
  | "select-aux"
  | "select-named-coast"
  | "completed";
export type NullEnum = null;
export type OrderRead = {
  source: ProvinceRead;
  target: ProvinceRead;
  aux: ProvinceRead;
  namedCoast: ProvinceRead;
  resolution: OrderResolutionRead;
  options: OrderOption[];
  orderType: OrderTypeEnum;
  unitType: UnitTypeEnum;
  nation: Nation;
  complete: boolean | null;
  step: (StepEnum | NullEnum) | null;
  title: string | null;
  summary: string | null;
  selected?: string[];
};
export type Channel = {};
export type ChannelMessage = {
  body: string;
};
export type ChannelMember = {
  id: number;
  username: string;
  name: string;
  picture: string;
  nation: Nation;
};
export type ChannelMemberRead = {
  id: number;
  username: string;
  name: string;
  picture: string;
  nation: Nation;
  isCurrentUser: boolean;
};
export type ChannelMessageRead = {
  id: number;
  body: string;
  sender: ChannelMemberRead;
  createdAt: string;
};
export type ChannelRead = {
  id: number;
  name: string;
  private: boolean;
  messages: ChannelMessageRead[];
};
export type ChannelWrite = {
  memberIds: number[];
};
export type PhaseResolveResponse = {
  resolved: number;
  failed: number;
};
export type UserProfile = {
  id: number;
  name: string;
  picture: string;
  username: string;
  email: string;
};
export type Version = {
  environment: string;
  version: string;
};
export const {
  useApiSchemaRetrieveQuery,
  useApiTokenRefreshCreateMutation,
  useAuthLoginCreateMutation,
  useDevicesListQuery,
  useDevicesCreateMutation,
  useDevicesUpdateMutation,
  useGameCreateMutation,
  useGameRetrieveQuery,
  useGameConfirmPhaseUpdateMutation,
  useGameConfirmPhasePartialUpdateMutation,
  useGameJoinCreateMutation,
  useGameLeaveDestroyMutation,
  useGameOrdersCreateMutation,
  useGameOrdersListQuery,
  useGameOrdersDeleteDestroyMutation,
  useGamePhaseStateRetrieveQuery,
  useGamesListQuery,
  useGamesChannelsListQuery,
  useGamesChannelsMessagesCreateCreateMutation,
  useGamesChannelsCreateCreateMutation,
  usePhaseResolveCreateMutation,
  useUserRetrieveQuery,
  useVariantsListQuery,
  useVersionRetrieveQuery,
} = injectedRtkApi;
