import React from "react";
import { Avatar, AvatarImage } from "@/components/ui/avatar";

interface AuthLayoutProps {
  children: React.ReactNode;
}

const AuthLayout: React.FC<AuthLayoutProps> = ({ children }) => {
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
        {children}
      </div>
    </div>
  );
};

export { AuthLayout };
