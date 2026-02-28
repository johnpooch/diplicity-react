import { SocialLogin } from "@capgo/capacitor-social-login";

export async function initializeNativeGoogleAuth(): Promise<void> {
  await SocialLogin.initialize({
    google: {
      iOSClientId: import.meta.env.VITE_GOOGLE_IOS_CLIENT_ID,
      webClientId: import.meta.env.VITE_GOOGLE_CLIENT_ID,
      mode: "online",
    },
  });
}

export async function nativeGoogleSignIn(): Promise<string> {
  const { result } = await SocialLogin.login({
    provider: "google",
    options: {},
  });
  if (result.responseType !== "online") {
    throw new Error("Expected online login response");
  }
  if (!result.idToken) {
    throw new Error("No ID token received from native Google Sign-In");
  }
  return result.idToken;
}
