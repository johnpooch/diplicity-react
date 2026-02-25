import React from "react";
import { CredentialResponse, GoogleLogin } from "@react-oauth/google";
import { toast } from "sonner";
import { useAuth } from "../auth";
import { useAuthLoginCreate } from "../api/generated/endpoints";
import { Avatar, AvatarImage } from "@/components/ui/avatar";
import { isNativePlatform } from "@/utils/platform";
import { nativeGoogleSignIn } from "@/auth/nativeGoogleAuth";
import { Button } from "@/components/ui/button";

const Login: React.FC = () => {
  const { login } = useAuth();
  const loginMutation = useAuthLoginCreate();

  const sendIdTokenToBackend = async (idToken: string) => {
    const result = await loginMutation.mutateAsync({
      data: { idToken },
    });
    login({
      accessToken: result.accessToken,
      refreshToken: result.refreshToken,
      email: result.email,
      name: result.name,
    });
    toast.success(`Logged in as ${result.name}`);
  };

  const handleWebLoginSuccess = async (credentialResponse: CredentialResponse) => {
    if (!credentialResponse.credential) {
      console.error("No credential response received");
      return;
    }
    try {
      await sendIdTokenToBackend(credentialResponse.credential);
    } catch {
      toast.error("Login failed");
    }
  };

  const handleWebLoginError = () => {
    console.error("Login failed");
    toast.error("Login failed");
  };

  const handleNativeLogin = async () => {
    try {
      const idToken = await nativeGoogleSignIn();
      await sendIdTokenToBackend(idToken);
    } catch {
      toast.error("Login failed");
    }
  };

  return (
    <div
      className="flex justify-center items-center h-screen bg-cover bg-no-repeat"
      style={{ backgroundImage: "url('/login_background.jpg')", backgroundPosition: "54%" }}
    >
      <div className="flex flex-col items-center gap-4 p-8 bg-background rounded">
        <Avatar className="size-12">
          <AvatarImage src="/otto.png" alt="Diplicity Logo" />
        </Avatar>
        <h1 className="text-base">Welcome to Diplicity!</h1>
        <p className="text-sm text-muted-foreground">
          A digital adaptation of the game of Diplomacy.
        </p>
        <div className="flex justify-center mt-2">
          {isNativePlatform() ? (
            <Button onClick={handleNativeLogin}>Sign in with Google</Button>
          ) : (
            <GoogleLogin
              onSuccess={handleWebLoginSuccess}
              onError={handleWebLoginError}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export { Login };
