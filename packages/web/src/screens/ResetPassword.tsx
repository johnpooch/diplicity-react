import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Link, useSearchParams } from "react-router";
import { useAuthPasswordResetConfirmCreate } from "@/api/generated/endpoints";
import { AuthLayout } from "@/components/AuthLayout";
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
    <AuthLayout>
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
    </AuthLayout>
  );
};

export { ResetPassword };
