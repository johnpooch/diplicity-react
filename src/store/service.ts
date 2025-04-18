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
        body: queryArg.loginRequest,
      }),
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
    gameCreate: build.mutation<GameCreateApiResponse, GameCreateApiArg>({
      query: (queryArg) => ({
        url: `/game/`,
        method: "POST",
        body: queryArg.gameCreateRequest,
      }),
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
    gameOrderCreate: build.mutation<
      GameOrderCreateApiResponse,
      GameOrderCreateApiArg
    >({
      query: (queryArg) => ({
        url: `/game/${queryArg.gameId}/order/`,
        method: "POST",
        body: queryArg.orderCreateRequest,
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
    variantsList: build.query<VariantsListApiResponse, VariantsListApiArg>({
      query: () => ({ url: `/variants/` }),
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
export type AuthLoginCreateApiResponse = /** status 200  */ LoginResponse;
export type AuthLoginCreateApiArg = {
  loginRequest: LoginRequest;
};
export type DevicesCreateApiResponse = /** status 201  */ FcmDeviceRead;
export type DevicesCreateApiArg = {
  fcmDevice: FcmDevice;
};
export type GameCreateApiResponse = /** status 201  */ GameCreateRequest;
export type GameCreateApiArg = {
  gameCreateRequest: GameCreateRequest;
};
export type GameConfirmCreateApiResponse = unknown;
export type GameConfirmCreateApiArg = {
  gameId: number;
};
export type GameJoinCreateApiResponse = unknown;
export type GameJoinCreateApiArg = {
  gameId: number;
};
export type GameLeaveDestroyApiResponse = unknown;
export type GameLeaveDestroyApiArg = {
  gameId: number;
};
export type GameOrderCreateApiResponse = /** status 201  */ OrderCreateRequest;
export type GameOrderCreateApiArg = {
  gameId: number;
  orderCreateRequest: OrderCreateRequest;
};
export type GamesListApiResponse = /** status 200  */ GameListResponseRead[];
export type GamesListApiArg = {
  canJoin?: boolean;
  mine?: boolean;
};
export type VariantsListApiResponse = /** status 200  */ VariantListResponse[];
export type VariantsListApiArg = void;
export type TokenRefresh = {};
export type TokenRefreshRead = {
  access: string;
};
export type TokenRefreshWrite = {
  refresh: string;
};
export type LoginResponse = {
  id: string;
  email: string;
  username: string;
  accessToken: string;
  refreshToken: string;
};
export type LoginRequest = {
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
export type GameCreateRequest = {
  name: string;
  variant: string;
};
export type OrderCreateRequest = {
  orderType: string;
  source: string;
  target?: string | null;
  aux?: string | null;
};
export type CurrentPhaseUnits = {
  type: string;
  nation: string;
  province: string;
};
export type CurrentPhaseSupplyCenters = {
  province: string;
  nation: string;
};
export type CurrentPhase = {
  season: string;
  year: string;
  phaseType: string;
  remainingTime: string;
  units: CurrentPhaseUnits[];
  supplyCenters: CurrentPhaseSupplyCenters[];
};
export type GameVariantNations = {
  name: string;
  color: string;
};
export type Variant = {
  id: string;
  name: string;
  description: string;
  author: string;
  nations: GameVariantNations[];
};
export type User = {
  username: string;
};
export type UserRead = {
  username: string;
  currentUser: boolean;
};
export type Members = {
  user: User;
  nation: string;
};
export type MembersRead = {
  user: UserRead;
  nation: string;
};
export type GameListResponse = {
  id: number;
  name: string;
  status: string;
  movementPhaseDuration: string;
  currentPhase: CurrentPhase;
  variant: Variant;
  members: Members[];
};
export type GameListResponseRead = {
  id: number;
  name: string;
  status: string;
  movementPhaseDuration: string;
  currentPhase: CurrentPhase;
  variant: Variant;
  members: MembersRead[];
};
export type VariantNations = {
  name: string;
  color: string;
};
export type VariantStartUnits = {
  type: string;
  nation: string;
  province: string;
};
export type VariantStartSupplyCenters = {
  province: string;
  nation: string;
};
export type VariantStart = {
  season: string;
  year: string;
  phaseType: string;
  units: VariantStartUnits[];
  supplyCenters: VariantStartSupplyCenters[];
};
export type VariantListResponse = {
  id: string;
  name: string;
  description: string;
  author?: string;
  nations: VariantNations[];
  start: VariantStart;
};
export const {
  useApiSchemaRetrieveQuery,
  useApiTokenRefreshCreateMutation,
  useAuthLoginCreateMutation,
  useDevicesCreateMutation,
  useGameCreateMutation,
  useGameConfirmCreateMutation,
  useGameJoinCreateMutation,
  useGameLeaveDestroyMutation,
  useGameOrderCreateMutation,
  useGamesListQuery,
  useVariantsListQuery,
} = injectedRtkApi;
