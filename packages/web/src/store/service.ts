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
        body: queryArg.authLoginRequest,
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
        body: queryArg.gameCreateRequest,
      }),
    }),
    gameRetrieve: build.query<GameRetrieveApiResponse, GameRetrieveApiArg>({
      query: (queryArg) => ({ url: `/game/${queryArg.gameId}/` }),
    }),
    gameChannelCreate: build.mutation<
      GameChannelCreateApiResponse,
      GameChannelCreateApiArg
    >({
      query: (queryArg) => ({
        url: `/game/${queryArg.gameId}/channel/`,
        method: "POST",
        body: queryArg.channelCreateRequest,
      }),
    }),
    gameChannelCreate2: build.mutation<
      GameChannelCreate2ApiResponse,
      GameChannelCreate2ApiArg
    >({
      query: (queryArg) => ({
        url: `/game/${queryArg.gameId}/channel/${queryArg.channelId}/`,
        method: "POST",
        body: queryArg.channelMessageCreateRequest,
      }),
    }),
    gameChannelsList: build.query<
      GameChannelsListApiResponse,
      GameChannelsListApiArg
    >({
      query: (queryArg) => ({ url: `/game/${queryArg.gameId}/channels/` }),
    }),
    gameConfirmCreate: build.mutation<
      GameConfirmCreateApiResponse,
      GameConfirmCreateApiArg
    >({
      query: (queryArg) => ({
        url: `/game/${queryArg.gameId}/confirm/`,
        method: "POST",
      }),
    }),
    gameJoinCreate: build.mutation<
      GameJoinCreateApiResponse,
      GameJoinCreateApiArg
    >({
      query: (queryArg) => ({
        url: `/game/${queryArg.gameId}/join/`,
        method: "POST",
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
    gameOrderableProvincesList: build.query<
      GameOrderableProvincesListApiResponse,
      GameOrderableProvincesListApiArg
    >({
      query: (queryArg) => ({
        url: `/game/${queryArg.gameId}/orderable-provinces/`,
      }),
    }),
    gameOrdersCreateInteractiveCreate: build.mutation<
      GameOrdersCreateInteractiveCreateApiResponse,
      GameOrdersCreateInteractiveCreateApiArg
    >({
      query: (queryArg) => ({
        url: `/game/${queryArg.gameId}/orders/create-interactive/`,
        method: "POST",
        body: queryArg.interactiveOrderCreateRequest,
      }),
    }),
    gamePhaseOptionsCreate: build.mutation<
      GamePhaseOptionsCreateApiResponse,
      GamePhaseOptionsCreateApiArg
    >({
      query: (queryArg) => ({
        url: `/game/${queryArg.gameId}/phase/${queryArg.phaseId}/options/`,
        method: "POST",
        body: queryArg.listOptionsRequest,
      }),
    }),
    gamePhaseOrdersList: build.query<
      GamePhaseOrdersListApiResponse,
      GamePhaseOrdersListApiArg
    >({
      query: (queryArg) => ({
        url: `/game/${queryArg.gameId}/phase/${queryArg.phaseId}/orders/`,
      }),
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
export type AuthLoginCreateApiResponse = /** status 200  */ Auth;
export type AuthLoginCreateApiArg = {
  authLoginRequest: AuthLoginRequest;
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
  gameCreateRequest: GameCreateRequest;
};
export type GameRetrieveApiResponse = /** status 200  */ GameRead;
export type GameRetrieveApiArg = {
  gameId: string;
};
export type GameChannelCreateApiResponse = /** status 201  */ Channel;
export type GameChannelCreateApiArg = {
  gameId: string;
  channelCreateRequest: ChannelCreateRequest;
};
export type GameChannelCreate2ApiResponse = /** status 201  */ Channel;
export type GameChannelCreate2ApiArg = {
  channelId: number;
  gameId: string;
  channelMessageCreateRequest: ChannelMessageCreateRequest;
};
export type GameChannelsListApiResponse = /** status 200  */ Channel[];
export type GameChannelsListApiArg = {
  gameId: string;
};
export type GameConfirmCreateApiResponse = /** status 200  */ GameRead;
export type GameConfirmCreateApiArg = {
  gameId: string;
};
export type GameJoinCreateApiResponse = /** status 200  */ GameRead;
export type GameJoinCreateApiArg = {
  gameId: string;
};
export type GameLeaveDestroyApiResponse = unknown;
export type GameLeaveDestroyApiArg = {
  gameId: string;
};
export type GameOrderableProvincesListApiResponse =
  /** status 200  */ OrderableProvinceListResponse[];
export type GameOrderableProvincesListApiArg = {
  gameId: string;
};
export type GameOrdersCreateInteractiveCreateApiResponse =
  /** status 200  */ InteractiveOrderCreateResponse;
export type GameOrdersCreateInteractiveCreateApiArg = {
  gameId: string;
  interactiveOrderCreateRequest: InteractiveOrderCreateRequest;
};
export type GamePhaseOptionsCreateApiResponse = /** status 200  */ Option[];
export type GamePhaseOptionsCreateApiArg = {
  gameId: string;
  phaseId: number;
  listOptionsRequest: ListOptionsRequest;
};
export type GamePhaseOrdersListApiResponse =
  /** status 200  */ OrderListResponse[];
export type GamePhaseOrdersListApiArg = {
  gameId: string;
  phaseId: number;
};
export type GamesListApiResponse = /** status 200  */ GameRead[];
export type GamesListApiArg = {
  canJoin?: boolean;
  mine?: boolean;
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
export type Auth = {
  id: number;
  email: string;
  username: string;
  accessToken: string;
  refreshToken: string;
};
export type AuthLoginRequest = {
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
export type PhaseNation = {
  name: string;
};
export type Province = {
  id: string;
  name: string;
  type: string;
  supplyCenter: boolean;
};
export type Unit = {
  type: string;
  nation: PhaseNation;
  province: Province;
};
export type SupplyCenter = {
  province: Province;
  nation: PhaseNation;
};
export type StatusEnum = "pending" | "active" | "completed";
export type Phase = {
  id: number;
  ordinal: number;
  season: string;
  year: number;
  name: string;
  type: string;
  units: Unit[];
  supplyCenters: SupplyCenter[];
  options: {
    [key: string]: any;
  };
  status: StatusEnum;
};
export type PhaseRead = {
  id: number;
  ordinal: number;
  season: string;
  year: number;
  name: string;
  type: string;
  remainingTime: string;
  units: Unit[];
  supplyCenters: SupplyCenter[];
  options: {
    [key: string]: any;
  };
  status: StatusEnum;
};
export type Member = {
  id: number;
  username: string;
  name: string;
  picture: string;
  nation: string;
  isCurrentUser: boolean;
};
export type Nation = {
  name: string;
  color: string;
};
export type Start = {
  season: string;
  year: string;
  type: string;
  units: {
    [key: string]: any;
  }[];
  supplyCenters: {
    [key: string]: any;
  }[];
};
export type Variant = {
  id: string;
  name: string;
  description: string;
  author?: string;
  nations: Nation[];
  start: Start;
  provinces: Province[];
  initialPhase: Phase;
};
export type VariantRead = {
  id: string;
  name: string;
  description: string;
  author?: string;
  nations: Nation[];
  start: Start;
  provinces: Province[];
  initialPhase: PhaseRead;
};
export type Game = {
  id: string;
  name: string;
  status: string;
  movementPhaseDuration: string;
  nationAssignment: string;
  canJoin: boolean;
  canLeave: boolean;
  phases: Phase[];
  members: Member[];
  variant: Variant;
  phaseConfirmed: boolean;
  canConfirmPhase: boolean;
};
export type GameRead = {
  id: string;
  name: string;
  status: string;
  movementPhaseDuration: string;
  nationAssignment: string;
  canJoin: boolean;
  canLeave: boolean;
  phases: PhaseRead[];
  members: Member[];
  variant: VariantRead;
  phaseConfirmed: boolean;
  canConfirmPhase: boolean;
};
export type NationAssignmentEnum = "random" | "ordered";
export type GameCreateRequest = {
  name: string;
  variant: string;
  nationAssignment?: NationAssignmentEnum;
};
export type Sender = {
  id: number;
  username: string;
  nation: Nation;
  isCurrentUser: boolean;
};
export type Message = {
  id: number;
  body: string;
  sender: Sender;
  createdAt: string;
};
export type Channel = {
  id: number;
  name: string;
  private: boolean;
  messages: Message[];
};
export type ChannelCreateRequest = {
  members: number[];
};
export type ChannelMessageCreateRequest = {
  body: string;
};
export type OrderProvince = {
  id: string;
  name: string;
  type: string;
  supplyCenter: boolean;
};
export type OrderResolution = {
  status: string;
  by: string | null;
};
export type Order = {
  id: number;
  orderType: string;
  source: OrderProvince;
  target: OrderProvince | null;
  aux: OrderProvince | null;
  resolution: OrderResolution | null;
};
export type OrderableProvinceListResponse = {
  province: OrderProvince;
  order: Order | null;
};
export type OrderOption = {
  value: string;
  label: string;
};
export type InteractiveOrderCreateResponse = {
  options: OrderOption[];
  step: string;
  title: string;
  completed: boolean;
  selected: string[];
  createdOrder?: Order | null;
};
export type InteractiveOrderCreateRequest = {
  /** Array of selected options representing the current order path */
  selected: string[];
};
export type Option = {
  province: Province;
  unit?: Unit | null;
};
export type PartialOrder = {
  source?: string | null;
  target?: string | null;
  aux?: string | null;
  orderType?: string | null;
};
export type ListOptionsRequest = {
  order: PartialOrder;
};
export type OrderListResponse = {
  nation: string;
  orders: Order[];
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
  useGameChannelCreateMutation,
  useGameChannelCreate2Mutation,
  useGameChannelsListQuery,
  useGameConfirmCreateMutation,
  useGameJoinCreateMutation,
  useGameLeaveDestroyMutation,
  useGameOrderableProvincesListQuery,
  useGameOrdersCreateInteractiveCreateMutation,
  useGamePhaseOptionsCreateMutation,
  useGamePhaseOrdersListQuery,
  useGamesListQuery,
  useUserRetrieveQuery,
  useVariantsListQuery,
  useVersionRetrieveQuery,
} = injectedRtkApi;
