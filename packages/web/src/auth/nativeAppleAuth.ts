import { SocialLogin } from "@capgo/capacitor-social-login";

interface AppleSignInResult {
  idToken: string;
  firstName?: string;
  lastName?: string;
}

export async function nativeAppleSignIn(): Promise<AppleSignInResult> {
  const { result } = await SocialLogin.login({
    provider: "apple",
    options: {
      scopes: ["email", "name"],
    },
  });
  if (!result.idToken) {
    throw new Error("No ID token received from Apple Sign-In");
  }
  return {
    idToken: result.idToken,
    firstName: result.profile?.givenName ?? undefined,
    lastName: result.profile?.familyName ?? undefined,
  };
}
