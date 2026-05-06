import React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { CredentialResponse, GoogleLogin } from "@react-oauth/google";
import { Link } from "react-router";
import { toast } from "sonner";
import { ChevronDown } from "lucide-react";
import { useAuth } from "../auth";
import {
  useAuthAppleLoginCreate,
  useAuthEmailLoginCreate,
  useAuthLoginCreate,
} from "../api/generated/endpoints";
import { isNativePlatform } from "@/utils/platform";
import { nativeAppleSignIn } from "@/auth/nativeAppleAuth";
import { nativeGoogleSignIn } from "@/auth/nativeGoogleAuth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarImage } from "@/components/ui/avatar";
import { GuideContent } from "@/components/GuideContent";
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
    <div className="w-full bg-background">
      {/* HERO */}
      <section
        id="top"
        className="relative flex flex-col lg:flex-row lg:items-center lg:justify-between min-h-dvh lg:h-dvh lg:min-h-[600px] pt-24 pb-24 px-6 lg:pt-0 lg:pb-0 lg:px-[6vw] gap-10 lg:gap-[6vw] text-white overflow-hidden"
        style={{
          backgroundImage:
            "linear-gradient(180deg, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0.35) 50%, rgba(0,0,0,0.65) 100%), url('/login_background.jpg')",
          backgroundSize: "cover",
          backgroundPosition: "54% center",
        }}
      >
        {/* Grain overlay */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            backgroundImage:
              "radial-gradient(rgba(255,255,255,0.04) 1px, transparent 1px)",
            backgroundSize: "3px 3px",
          }}
        />

        {/* App bar */}
        <div className="absolute top-0 left-0 right-0 flex items-center justify-between px-6 lg:px-[6vw] py-5 z-10">
          <div className="flex items-center gap-3 font-semibold text-[18px] text-white">
            <div className="size-8 rounded-full bg-white overflow-hidden shrink-0">
              <img
                src="/otto.png"
                alt="Diplicity"
                className="w-full h-full object-cover"
              />
            </div>
            <span>Diplicity</span>
          </div>
          <div className="flex items-center gap-2">
            <Link
              to="/learn-to-play"
              className="hidden sm:inline-flex text-sm font-medium text-white/90 hover:text-white px-3 py-1.5 hover:bg-white/10 rounded-md transition-colors"
            >
              Learn to play
            </Link>
            <Link
              to="/register"
              className="text-sm font-medium border border-white/40 text-white px-3 py-1.5 rounded-md hover:bg-white/10 transition-colors"
            >
              Register
            </Link>
          </div>
        </div>

        {/* Marketing blurb — top on mobile, right on desktop */}
        <div className="relative z-10 order-1 lg:order-2 lg:max-w-[560px] text-center lg:text-left">
          <div className="text-xs tracking-[0.18em] uppercase text-white/70 mb-5">
            Play-by-email Diplomacy · Since 2014
          </div>
          <h2 className="text-[clamp(32px,5.5vw,68px)] leading-[1.05] font-semibold tracking-[-0.02em] text-white mb-6">
            Seven powers.
            <br />
            One map.
            <br />
            <em className="font-normal text-white/85">No dice.</em>
          </h2>
          <p className="text-[17px] leading-[1.6] text-white/85 max-w-[520px] mb-7 mx-auto lg:mx-0">
            Diplicity hosts the classic game of Diplomacy online — slow games
            measured in days, fast games measured in hours. Negotiate, ally, and
            betray your way to eighteen supply centers.
          </p>
          <div className="flex justify-center lg:justify-start gap-3">
            <Link
              to="/learn-to-play"
              className="inline-flex items-center justify-center h-11 px-6 text-[15px] font-medium border border-white/40 text-white rounded-md hover:bg-white/10 transition-colors"
            >
              Read the rules
            </Link>
          </div>
        </div>

        {/* Login card — bottom on mobile, left on desktop */}
        <div className="relative z-10 order-2 lg:order-1 w-full max-w-[380px] mx-auto lg:mx-0 lg:max-w-[360px]">
          <div className="bg-background text-foreground rounded-lg p-8 flex flex-col items-center gap-4 shadow-[0_20px_60px_rgba(0,0,0,0.35)]">
            <Avatar className="size-12">
              <AvatarImage src="/otto.png" alt="Diplicity Logo" />
            </Avatar>
            <h1 className="text-base font-semibold">Welcome to Diplicity!</h1>
            <p className="text-sm text-muted-foreground text-center -mt-2">
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
                        <Input
                          type="email"
                          placeholder="you@example.com"
                          {...field}
                        />
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
                        <Input
                          type="password"
                          placeholder="••••••••"
                          {...field}
                        />
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
          </div>
        </div>

        {/* Scroll hint */}
        <a
          href="#guide"
          className="absolute left-1/2 bottom-8 -translate-x-1/2 z-10 hidden md:flex flex-col items-center gap-2.5 text-white/75 text-xs tracking-[0.16em] uppercase no-underline hover:text-white transition-colors"
        >
          <span>Learn how to play</span>
          <ChevronDown className="size-5 animate-bounce" />
        </a>
      </section>

      {/* Guide intro */}
      <section id="guide" className="px-6 pt-24 pb-12 text-center bg-background">
        <div className="text-xs tracking-[0.18em] uppercase text-muted-foreground mb-[18px]">
          Quick-start guide · 5 minute read
        </div>
        <h2 className="text-[clamp(36px,4.5vw,56px)] font-semibold tracking-[-0.01em] leading-[1.15] max-w-[16ch] mx-auto mb-5">
          Learn the rules in five minutes.
        </h2>
        <p className="text-[18px] leading-[1.6] text-muted-foreground max-w-[600px] mx-auto">
          Diplomacy looks like a war game. It isn&apos;t — at least not in the
          usual sense. The board is a stage; the real game is the conversation
          around it.
        </p>
      </section>

      {/* Guide content */}
      <GuideContent />

      {/* End CTA */}
      <section className="text-center py-24 px-6 border-t border-border bg-secondary">
        <div className="text-xs tracking-[0.18em] uppercase text-muted-foreground mb-4">
          Ready when you are
        </div>
        <h2 className="text-[clamp(28px,3.5vw,40px)] font-semibold tracking-[-0.01em] leading-[1.15] max-w-[18ch] mx-auto mb-7">
          Find seven players. Or seven enemies. Same thing.
        </h2>
        <a
          href="#top"
          className="inline-flex items-center justify-center h-11 px-6 text-[15px] font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
        >
          Sign in to play
        </a>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 border-t border-border text-center text-sm text-muted-foreground">
        <div>Diplicity · 2014–2026</div>
        <div className="mt-2 flex justify-center gap-5">
          <Link to="/learn-to-play" className="hover:text-foreground transition-colors">
            Rules
          </Link>
          <a
            href="https://diplicity.notion.site/Diplicity-FAQ-7b4e0a119eb54c69b80b411f14d43bb9"
            target="_blank"
            rel="noreferrer"
            className="hover:text-foreground transition-colors"
          >
            FAQ
          </a>
          <a
            href="https://github.com/johnpooch/diplicity-react"
            target="_blank"
            rel="noreferrer"
            className="hover:text-foreground transition-colors"
          >
            GitHub
          </a>
        </div>
      </footer>
    </div>
  );
};

export { Login };
