export interface AppleAuthResponse {
  authorization?: {
    id_token?: string;
  };
  user?: {
    name?: {
      firstName?: string;
      lastName?: string;
    };
  };
}

interface AppleSignInResult {
  idToken: string;
  firstName?: string;
  lastName?: string;
}

export const webAppleAuthOptions = {
  clientId: import.meta.env.VITE_APPLE_WEB_CLIENT_ID,
  redirectURI: import.meta.env.VITE_APPLE_REDIRECT_URI,
  scope: "name email",
  usePopup: true,
};

export function parseAppleResponse(response: AppleAuthResponse): AppleSignInResult {
  const idToken = response.authorization?.id_token;
  if (!idToken) {
    throw new Error("No ID token received from Apple Sign-In");
  }
  return {
    idToken,
    firstName: response.user?.name?.firstName ?? undefined,
    lastName: response.user?.name?.lastName ?? undefined,
  };
}
