import React from "react";
import { Link } from "react-router";
import { AuthLayout } from "@/components/AuthLayout";
import { Mail } from "lucide-react";

const CheckEmail: React.FC = () => {
  return (
    <AuthLayout>
      <Mail className="size-10 text-muted-foreground" />
      <h1 className="text-base">Check your email</h1>
      <p className="text-sm text-muted-foreground text-center">
        We&apos;ve sent a verification link to your email address. Click the
        link to activate your account.
      </p>
      <Link to="/" className="text-sm text-primary hover:underline">
        Back to Sign In
      </Link>
    </AuthLayout>
  );
};

export { CheckEmail };
