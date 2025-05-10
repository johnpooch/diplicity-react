import { telemetry } from "./telemetry";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { GoogleSignin } from "@react-native-google-signin/google-signin";

interface IAuthService {
    getTokenFromStorage: () => Promise<string | null>;
    getServerAuthCode: () => Promise<string>;
    getCallbackUrl: (serverAuthCode: string) => Promise<string>;
    getTokenFromRedirectUrl: (redirectUrl: string) => string;
    removeTokenFromStorage: () => Promise<void>;
    setTokenInStorage: (token: string) => Promise<void>;
}

const serviceUrl = "https://diplicity-engine.appspot.com/";

class AuthService implements IAuthService {
    constructor() {
        GoogleSignin.configure({
            webClientId:
                "635122585664-ao5i9f2p5365t4htql1qdb6uulso4929.apps.googleusercontent.com",
            offlineAccess: true,
        });
    }
    public async getTokenFromStorage() {
        telemetry.logInfo("Reading token from storage");
        const token = await AsyncStorage.getItem("token");
        telemetry.logInfo(`Token is in storage: ${Boolean(token)}`);
        return token;
    }
    public async setTokenInStorage(token: string) {
        telemetry.logInfo("Setting token in storage");
        await AsyncStorage.setItem("token", token);
        telemetry.logInfo("Token set in storage");
    }
    public async removeTokenFromStorage() {
        telemetry.logInfo("Setting token in storage");
        await AsyncStorage.removeItem("token");
        telemetry.logInfo("Token set in storage");
    }
    public async getCallbackUrl(serverAuthCode: string) {
        const encodedServerAuthCode = encodeURIComponent(serverAuthCode);
        const encodedState = encodeURIComponent(serviceUrl);
        return `${serviceUrl}Auth/OAuth2Callback?code=${encodedServerAuthCode}&approve-redirect=true&state=${encodedState}`;
    }
    public getTokenFromRedirectUrl(redirectUrl: string) {
        const decodedRedirectUrl = decodeURIComponent(redirectUrl);
        const match = decodedRedirectUrl.match(/token=([^&]*)/);
        if (!match) {
            throw new Error("Could not get token from decoded redirect URL");
        }
        return match[1];
    }
    public async getServerAuthCode() {
        try {
            telemetry.logInfo("Checking if user has play services");
            const hasPlayServices = await GoogleSignin.hasPlayServices();
            telemetry.logInfo(`Has play services: ${hasPlayServices}`);

            telemetry.logInfo("Signing in");
            const userInfo = await GoogleSignin.signIn();
            telemetry.logInfo("Signed in");

            if (!userInfo.data) {
                throw new Error("User info is null");
            }

            telemetry.logInfo("Checking server auth code");
            const { serverAuthCode } = userInfo.data;
            if (!serverAuthCode) {
                throw new Error("Server auth code is null");
            }
            telemetry.logInfo("Server auth code is not null");
            return serverAuthCode;
        } catch (error) {
            if (error instanceof Error) {
                telemetry.logError(
                    `Error thrown while signing in: ${error.message}`
                );
            } else {
                telemetry.logError("Error is not an instance of Error");
            }
            throw error;
        }
    }
}

const authService = new AuthService();

export { authService };
