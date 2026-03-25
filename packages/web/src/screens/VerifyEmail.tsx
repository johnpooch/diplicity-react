import React, { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router";
import { useAuthVerifyEmailCreate } from "../api/generated/endpoints";
import { Avatar, AvatarImage } from "@/components/ui/avatar";

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
      </div>
    </div>
  );
};

export { VerifyEmail };
