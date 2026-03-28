import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Link, useSearchParams } from "react-router";
import { useAuthPasswordResetConfirmCreate } from "@/api/generated/endpoints";
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

const resetPasswordSchema = z
  .object({
    newPassword: z.string().min(8, "Password must be at least 8 characters"),
    confirmPassword: z
      .string()
      .min(8, "Password must be at least 8 characters"),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

type ResetPasswordFormValues = z.infer<typeof resetPasswordSchema>;

const ResetPassword: React.FC = () => {
  const [searchParams] = useSearchParams();
  const uid = searchParams.get("uid");
  const token = searchParams.get("token");
  const mutation = useAuthPasswordResetConfirmCreate();
  const [status, setStatus] = useState<"form" | "success" | "error">(
    uid && token ? "form" : "error"
  );

  const form = useForm<ResetPasswordFormValues>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: { newPassword: "", confirmPassword: "" },
  });

  const handleSubmit = async (data: ResetPasswordFormValues) => {
    try {
      await mutation.mutateAsync({
        data: {
          uid: uid!,
          token: token!,
          newPassword: data.newPassword,
          confirmPassword: data.confirmPassword,
        },
      });
      setStatus("success");
    } catch {
      setStatus("error");
    }
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

        {status === "form" && (
          <>
            <h1 className="text-base">Reset your password</h1>

            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(handleSubmit)}
                className="w-full space-y-4"
              >
                <FormField
                  control={form.control}
                  name="newPassword"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>New Password</FormLabel>
                      <FormControl>
                        <Input type="password" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="confirmPassword"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Confirm Password</FormLabel>
                      <FormControl>
                        <Input type="password" {...field} />
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
                  Reset Password
                </Button>
              </form>
            </Form>
          </>
        )}

        {status === "success" && (
          <>
            <h1 className="text-base">Password reset!</h1>
            <p className="text-sm text-muted-foreground text-center">
              Your password has been updated. You can now sign in.
            </p>
            <Link to="/" className="text-sm text-primary hover:underline">
              Sign In
            </Link>
          </>
        )}

        {status === "error" && (
          <>
            <h1 className="text-base">Reset failed</h1>
            <p className="text-sm text-muted-foreground text-center">
              The reset link is invalid or has expired.
            </p>
            <Link to="/" className="text-sm text-primary hover:underline">
              Back to Sign In
            </Link>
          </>
        )}
      </div>
    </div>
  );
};

export { ResetPassword };
