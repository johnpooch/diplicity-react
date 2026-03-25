import React from "react";
import { Link } from "react-router";
import { Avatar, AvatarImage } from "@/components/ui/avatar";
import { Mail } from "lucide-react";

const CheckEmail: React.FC = () => {
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
        <Mail className="size-10 text-muted-foreground" />
        <h1 className="text-base">Check your email</h1>
        <p className="text-sm text-muted-foreground text-center">
          We&apos;ve sent a verification link to your email address. Click the
          link to activate your account.
        </p>
        <Link to="/" className="text-sm text-primary hover:underline">
          Back to Sign In
        </Link>
      </div>
    </div>
  );
};

export { CheckEmail };
