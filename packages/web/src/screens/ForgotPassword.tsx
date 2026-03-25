import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Link } from "react-router";
import { Mail } from "lucide-react";
import { useAuthPasswordResetCreate } from "@/api/generated/endpoints";
import { Avatar, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";

const forgotPasswordSchema = z.object({
  email: z.string().email("Please enter a valid email"),
});

type ForgotPasswordFormValues = z.infer<typeof forgotPasswordSchema>;

const ForgotPassword: React.FC = () => {
  const [submitted, setSubmitted] = useState(false);
  const mutation = useAuthPasswordResetCreate();

  const form = useForm<ForgotPasswordFormValues>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: { email: "" },
  });

  const handleSubmit = async (data: ForgotPasswordFormValues) => {
    await mutation.mutateAsync({ data: { email: data.email } });
    setSubmitted(true);
  };

  return (
    <div
      className="flex justify-center items-center h-screen bg-cover bg-no-repeat pt-[var(--safe-area-top)] pb-[var(--safe-area-bottom)]"
      style={{
        backgroundImage: "url('/login_background.jpg')",
        backgroundPosition: "54%",
      }}
    >
      <div className="flex flex-col items-center gap-4 p-8 bg-background rounded w-80">
        <Avatar className="size-12">
          <AvatarImage src="/otto.png" alt="Diplicity Logo" />
        </Avatar>

        {submitted ? (
          <>
            <Mail className="size-10 text-muted-foreground" />
            <h1 className="text-base">Check your email</h1>
            <p className="text-sm text-muted-foreground text-center">
              If an account exists with that email, we&apos;ve sent a password
              reset link.
            </p>
          </>
        ) : (
          <>
            <h1 className="text-base">Forgot password?</h1>
            <p className="text-sm text-muted-foreground text-center">
              Enter your email and we&apos;ll send you a link to reset your
              password.
            </p>

            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(handleSubmit)}
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
                <Button
                  type="submit"
                  className="w-full"
                  disabled={mutation.isPending}
                >
                  Send Reset Link
                </Button>
              </form>
            </Form>
          </>
        )}

        <Link to="/" className="text-sm text-primary hover:underline">
          Back to Sign In
        </Link>
      </div>
    </div>
  );
};

export { ForgotPassword };
