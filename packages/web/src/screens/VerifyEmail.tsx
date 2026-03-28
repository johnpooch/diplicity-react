import React, { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router";
import { useAuthVerifyEmailCreate } from "../api/generated/endpoints";
import { AuthLayout } from "@/components/AuthLayout";

const VerifyEmail: React.FC = () => {
  const [searchParams] = useSearchParams();
  const verifyMutation = useAuthVerifyEmailCreate();
  const [status, setStatus] = useState<"verifying" | "success" | "error">(
    "verifying"
  );

  useEffect(() => {
    const uid = searchParams.get("uid");
    const token = searchParams.get("token");

    if (!uid || !token) {
      setStatus("error");
      return;
    }

    verifyMutation
      .mutateAsync({ data: { uid, token } })
      .then(() => setStatus("success"))
      .catch(() => setStatus("error"));
    // eslint-disable-next-line react-hooks/exhaustive-deps -- mutateAsync is stable, run once on mount
  }, [searchParams]);

  return (
    <AuthLayout>
        {status === "verifying" && (
          <p className="text-sm text-muted-foreground">
            Verifying your email...
          </p>
        )}

        {status === "success" && (
          <>
            <h1 className="text-base">Email verified!</h1>
            <p className="text-sm text-muted-foreground text-center">
              Your account is now active. You can sign in.
            </p>
            <Link to="/" className="text-sm text-primary hover:underline">
              Sign In
            </Link>
          </>
        )}

        {status === "error" && (
          <>
            <h1 className="text-base">Verification failed</h1>
            <p className="text-sm text-muted-foreground text-center">
              The verification link is invalid or has expired.
            </p>
            <Link to="/" className="text-sm text-primary hover:underline">
              Back to Sign In
            </Link>
          </>
        )}
    </AuthLayout>
  );
};

export { VerifyEmail };
