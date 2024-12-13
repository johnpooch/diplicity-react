import { IAuthService } from "../common/services";

const AuthService: IAuthService = {
    getTokenFromStorage: async () => {
        return localStorage.getItem("token");
    },
    getServerAuthCode: async () => {
        return "serverAuthCode";
    },
    getCallbackUrl: async (serverAuthCode) => {
        return `http://localhost:3000/callback?code=${serverAuthCode}`;
    },
    getTokenFromRedirectUrl: (redirectUrl) => {
        const url = new URL(redirectUrl);
        return url.searchParams.get("code") || "";
    },
    removeTokenFromStorage: async () => {
        localStorage.removeItem("token");
    },
    setTokenInStorage: async (token) => {
        localStorage.setItem("token", token);
    },
}

export { AuthService }