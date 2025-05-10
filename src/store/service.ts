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
        body: queryArg.request,
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
    gameChannelMessageCreate: build.mutation<
      GameChannelMessageCreateApiResponse,
      GameChannelMessageCreateApiArg
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
    userRetrieve: build.query<UserRetrieveApiResponse, UserRetrieveApiArg>({
      query: () => ({ url: `/user/` }),
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
export type GameCreateApiResponse = /** status 201  */ Game;
export type GameCreateApiArg = {
  request: Request;
};
export type GameRetrieveApiResponse = /** status 200  */ Game;
export type GameRetrieveApiArg = {
  gameId: number;
};
export type GameChannelCreateApiResponse =
  /** status 201  */ ChannelCreateResponse;
export type GameChannelCreateApiArg = {
  gameId: number;
  channelCreateRequest: ChannelCreateRequest;
};
export type GameChannelMessageCreateApiResponse = unknown;
export type GameChannelMessageCreateApiArg = {
  channelId: number;
  gameId: number;
  channelMessageCreateRequest: ChannelMessageCreateRequest;
};
export type GameChannelsListApiResponse =
  /** status 200  */ ChannelListResponseRead[];
export type GameChannelsListApiArg = {
  gameId: number;
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
export type GamesListApiResponse = /** status 200  */ Game[];
export type GamesListApiArg = {
  canJoin?: boolean;
  mine?: boolean;
};
export type UserRetrieveApiResponse = /** status 200  */ UserProfile;
export type UserRetrieveApiArg = void;
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
export type Nation = {
  name: string;
  color: string;
};
export type Province = {
  id: string;
  name: string;
  type: string;
  supplyCenter: boolean;
};
export type Unit = {
  type: string;
  nation: Nation;
  province: Province;
};
export type SupplyCenter = {
  province: Province;
  nation: Nation;
};
export type Phase = {
  id: number;
  ordinal: number;
  season: string;
  year: string;
  name: string;
  type: string;
  remainingTime: string;
  units: Unit[];
  supplyCenters: SupplyCenter[];
};
export type Member = {
  id: number;
  username: string;
  name: string;
  picture: string;
  nation: string;
  isCurrentUser: boolean;
};
export type Variant = {
  id: string;
  name: string;
  description: string;
  author?: string;
  nations: Nation[];
};
export type Game = {
  id: number;
  name: string;
  status: string;
  movementPhaseDuration: string;
  canJoin: boolean;
  canLeave: boolean;
  currentPhase: Phase;
  members: Member[];
  variant: Variant;
};
export type Request = {
  name: string;
  variant: string;
};
export type ChannelCreateResponse = {
  id: number;
};
export type ChannelCreateRequest = {
  members: number[];
  id?: number;
};
export type ChannelMessageCreateRequest = {
  body: string;
};
export type MessageSenderUserProfile = {
  name: string;
  picture: string;
};
export type MessageSenderUser = {
  username: string;
  profile: MessageSenderUserProfile;
};
export type MessageSenderUserRead = {
  username: string;
  currentUser: boolean;
  profile: MessageSenderUserProfile;
};
export type MessageSender = {
  id: number;
  nation: string;
  user: MessageSenderUser;
};
export type MessageSenderRead = {
  id: number;
  nation: string;
  user: MessageSenderUserRead;
};
export type ChannelMessages = {
  id: number;
  body: string;
  sender: MessageSender;
  createdAt: string;
};
export type ChannelMessagesRead = {
  id: number;
  body: string;
  sender: MessageSenderRead;
  createdAt: string;
};
export type ChannelListResponse = {
  id: number;
  name: string;
  private: boolean;
  messages: ChannelMessages[];
};
export type ChannelListResponseRead = {
  id: number;
  name: string;
  private: boolean;
  messages: ChannelMessagesRead[];
};
export type OrderCreateRequest = {
  orderType: string;
  source: string;
  target?: string | null;
  aux?: string | null;
};
export type UserProfile = {
  id: number;
  name: string;
  picture: string;
  username: string;
  email: string;
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
  type: string;
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
  useDevicesListQuery,
  useDevicesCreateMutation,
  useDevicesUpdateMutation,
  useGameCreateMutation,
  useGameRetrieveQuery,
  useGameChannelCreateMutation,
  useGameChannelMessageCreateMutation,
  useGameChannelsListQuery,
  useGameConfirmCreateMutation,
  useGameJoinCreateMutation,
  useGameLeaveDestroyMutation,
  useGameOrderCreateMutation,
  useGamesListQuery,
  useUserRetrieveQuery,
  useVariantsListQuery,
} = injectedRtkApi;
