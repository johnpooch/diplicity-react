import React from "react";
import { CredentialResponse, GoogleLogin } from "@react-oauth/google";
import { toast } from "sonner";
import { useAuth } from "../auth";
import { useAuthLoginCreate } from "../api/generated/endpoints";
import { Avatar, AvatarImage } from "@/components/ui/avatar";

const Login: React.FC = () => {
  const { login } = useAuth();
  const loginMutation = useAuthLoginCreate();

  const handleLoginSuccess = async (credentialResponse: CredentialResponse) => {
    if (!credentialResponse.credential) {
      console.error("No credential response received");
      return;
    }
    try {
      const result = await loginMutation.mutateAsync({
        data: {
          idToken: credentialResponse.credential,
        },
      });
      login({
        accessToken: result.accessToken,
        refreshToken: result.refreshToken,
        email: result.email,
        name: result.name,
      });
      toast.success(`Logged in as ${result.name}`);
    } catch {
      toast.error("Login failed");
    }
  };

  const handleLoginError = () => {
    console.error("Login failed");
    toast.error("Login failed");
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
          <GoogleLogin
            onSuccess={handleLoginSuccess}
            onError={handleLoginError}
          />
        </div>
      </div>
    </div>
  );
};

export { Login };
