export interface IAuthService {
    getTokenFromStorage: () => Promise<string | null>;
    getServerAuthCode: () => Promise<string>;
    getCallbackUrl: (serverAuthCode: string) => Promise<string>;
    getTokenFromRedirectUrl: (redirectUrl: string) => string;
    removeTokenFromStorage: () => Promise<void>;
    setTokenInStorage: (token: string) => Promise<void>;
}