import React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { CredentialResponse, GoogleLogin } from "@react-oauth/google";
import { Link } from "react-router";
import { toast } from "sonner";
import { useAuth } from "../auth";
import {
  useAuthAppleLoginCreate,
  useAuthEmailLoginCreate,
  useAuthLoginCreate,
} from "../api/generated/endpoints";
import { AuthLayout } from "@/components/AuthLayout";
import { isNativePlatform } from "@/utils/platform";
import { nativeAppleSignIn } from "@/auth/nativeAppleAuth";
import { nativeGoogleSignIn } from "@/auth/nativeGoogleAuth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";


const loginSchema = z.object({
  email: z.string().email("Please enter a valid email"),
  password: z.string().min(1, "Password is required"),
});

type LoginFormValues = z.infer<typeof loginSchema>;

const Login: React.FC = () => {
  const { login } = useAuth();
  const appleLoginMutation = useAuthAppleLoginCreate();
  const emailLoginMutation = useAuthEmailLoginCreate();
  const googleLoginMutation = useAuthLoginCreate();

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  const handleEmailLogin = async (data: LoginFormValues) => {
    try {
      const result = await emailLoginMutation.mutateAsync({
        data: { email: data.email, password: data.password },
      });
      login({
        accessToken: result.accessToken,
        refreshToken: result.refreshToken,
        email: result.email,
        name: result.name,
      });
      toast.success(`Logged in as ${result.name}`);
    } catch {
      toast.error("Invalid email or password");
    }
  };

  const sendIdTokenToBackend = async (idToken: string) => {
    const result = await googleLoginMutation.mutateAsync({
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

  const handleWebLoginSuccess = async (
    credentialResponse: CredentialResponse
  ) => {
    if (!credentialResponse.credential) {
      return;
    }
    try {
      await sendIdTokenToBackend(credentialResponse.credential);
    } catch {
      toast.error("Login failed");
    }
  };

  const handleWebLoginError = () => {
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

  const handleAppleLogin = async () => {
    try {
      const { idToken, firstName, lastName } = await nativeAppleSignIn();
      const result = await appleLoginMutation.mutateAsync({
        data: { idToken, firstName, lastName },
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

  return (
    <AuthLayout>
        <h1 className="text-base">Welcome to Diplicity!</h1>
        <p className="text-sm text-muted-foreground">
          A digital adaptation of the game of Diplomacy.
        </p>

        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(handleEmailLogin)}
            className="w-full space-y-4"
          >
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email</FormLabel>
                  <FormControl>
                    <Input type="email" placeholder="you@example.com" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Password</FormLabel>
                  <FormControl>
                    <Input type="password" placeholder="••••••••" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <Button
              type="submit"
              className="w-full"
              disabled={emailLoginMutation.isPending}
            >
              Sign In
            </Button>
          </form>
        </Form>

        <Link
          to="/forgot-password"
          className="text-sm text-muted-foreground hover:underline"
        >
          Forgot password?
        </Link>

        <div className="flex items-center gap-4 w-full">
          <Separator className="flex-1" />
          <span className="text-sm text-muted-foreground">OR</span>
          <Separator className="flex-1" />
        </div>

        <div className="flex flex-col items-center gap-3">
          {isNativePlatform() ? (
            <>
              <Button variant="outline" onClick={handleNativeLogin}>
                Sign in with Google
              </Button>
              <Button variant="outline" onClick={handleAppleLogin}>
                Sign in with Apple
              </Button>
            </>
          ) : (
            <GoogleLogin
              onSuccess={handleWebLoginSuccess}
              onError={handleWebLoginError}
            />
          )}
        </div>

        <p className="text-sm text-muted-foreground">
          Don&apos;t have an account?{" "}
          <Link to="/register" className="text-primary hover:underline">
            Register
          </Link>
        </p>
    </AuthLayout>
  );
};

export { Login };
