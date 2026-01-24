type TokenState = {
  accessToken: string | null;
  refreshToken: string | null;
  email: string | null;
  name: string | null;
};

type TokenChangeListener = () => void;

const listeners: Set<TokenChangeListener> = new Set();

// Cache the token state to avoid creating new objects on every getTokenState call
// This is required for useSyncExternalStore to work correctly
let cachedState: TokenState = {
  accessToken: localStorage.getItem("accessToken"),
  refreshToken: localStorage.getItem("refreshToken"),
  email: localStorage.getItem("email"),
  name: localStorage.getItem("name"),
};

const updateCachedState = () => {
  cachedState = {
    accessToken: localStorage.getItem("accessToken"),
    refreshToken: localStorage.getItem("refreshToken"),
    email: localStorage.getItem("email"),
    name: localStorage.getItem("name"),
  };
};

const getTokenState = (): TokenState => cachedState;

const setTokens = (tokens: {
  accessToken: string;
  refreshToken: string;
  email: string;
  name: string;
}) => {
  localStorage.setItem("accessToken", tokens.accessToken);
  localStorage.setItem("refreshToken", tokens.refreshToken);
  localStorage.setItem("email", tokens.email);
  localStorage.setItem("name", tokens.name);
  updateCachedState();
  notifyListeners();
};

const updateAccessToken = (accessToken: string) => {
  localStorage.setItem("accessToken", accessToken);
  updateCachedState();
  notifyListeners();
};

const clearTokens = () => {
  localStorage.removeItem("accessToken");
  localStorage.removeItem("refreshToken");
  localStorage.removeItem("email");
  localStorage.removeItem("name");
  updateCachedState();
  notifyListeners();
};

const notifyListeners = () => {
  listeners.forEach(listener => listener());
};

const subscribe = (listener: TokenChangeListener) => {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
};

const isLoggedIn = () => !!localStorage.getItem("accessToken");

export const tokenStorage = {
  getTokenState,
  setTokens,
  updateAccessToken,
  clearTokens,
  subscribe,
  isLoggedIn,
};

export type { TokenState };
