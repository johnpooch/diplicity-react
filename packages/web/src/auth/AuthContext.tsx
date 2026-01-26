import { createContext, useContext, useSyncExternalStore } from "react";
import { tokenStorage, TokenState } from "./tokenStorage";

type AuthState = TokenState & {
  loggedIn: boolean;
};

type AuthContextType = AuthState & {
  login: (tokens: {
    accessToken: string;
    refreshToken: string;
    email: string;
    name: string;
  }) => void;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Cache the auth state to avoid infinite loops with useSyncExternalStore
let cachedAuthState: AuthState | null = null;
let lastTokenState: TokenState | null = null;

const getSnapshot = (): AuthState => {
  const state = tokenStorage.getTokenState();

  // Return cached state if token state reference hasn't changed
  if (lastTokenState === state && cachedAuthState !== null) {
    return cachedAuthState;
  }

  // Update cache when token state changes
  lastTokenState = state;
  cachedAuthState = {
    ...state,
    loggedIn: !!state.accessToken,
  };
  return cachedAuthState;
};

const subscribe = (callback: () => void) => {
  return tokenStorage.subscribe(callback);
};

const AuthProvider: React.FC<React.PropsWithChildren> = ({ children }) => {
  const authState = useSyncExternalStore(subscribe, getSnapshot);

  const login = (tokens: {
    accessToken: string;
    refreshToken: string;
    email: string;
    name: string;
  }) => {
    tokenStorage.setTokens(tokens);
  };

  const logout = () => {
    tokenStorage.clearTokens();
  };

  return (
    <AuthContext value={{ ...authState, login, logout }}>
      {children}
    </AuthContext>
  );
};

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

export { AuthProvider, useAuth };
