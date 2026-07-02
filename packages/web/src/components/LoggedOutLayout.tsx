import React from "react";
import { useNavigate } from "react-router";
import { cn } from "@/lib/utils";
import { Item, ItemMedia, ItemContent, ItemTitle } from "@/components/ui/item";
import { DiplicityLogo } from "@/components/DiplicityLogo";
import { SafeAreaView } from "@/components/SafeAreaView";
import { Button } from "@/components/ui/button";

interface LoggedOutLayoutProps {
  children: React.ReactNode;
  className?: string;
}

const LoggedOutLayout: React.FC<LoggedOutLayoutProps> = ({
  children,
  className,
}) => {
  const navigate = useNavigate();

  const loginActions = (
    <div className="flex gap-2">
      <Button className="flex-1" onClick={() => navigate("/register")}>
        Create account
      </Button>
      <Button
        variant="outline"
        className="flex-1"
        onClick={() => navigate("/login")}
      >
        Sign in
      </Button>
    </div>
  );

  return (
    <SafeAreaView
      className={cn("flex flex-col h-dvh w-full overflow-hidden", className)}
    >
      <div className="flex items-stretch flex-1 min-h-0 w-full">
        <aside className="hidden md:flex w-72 shrink-0 flex-col border-r p-6">
          <Item className="p-1">
            <ItemMedia variant="image">
              <DiplicityLogo />
            </ItemMedia>
            <ItemContent>
              <ItemTitle>Diplicity</ItemTitle>
            </ItemContent>
          </Item>
          <div className="mt-8 space-y-2">
            <h2 className="text-2xl font-bold leading-tight">
              Welcome to Diplicity
            </h2>
            <p className="text-sm text-muted-foreground">
              A digital adaptation of the game of Diplomacy.
            </p>
          </div>
          <div className="mt-6">{loginActions}</div>
        </aside>

        <main className="flex min-w-0 flex-1 flex-col">
          <div className="@container flex-1 overflow-y-auto">
            <div className="mx-auto w-full max-w-[672px] py-4 px-2">
              {children}
            </div>
          </div>
        </main>
      </div>

      <div className="border-t bg-background block md:hidden">
        <div className="p-3">{loginActions}</div>
      </div>
    </SafeAreaView>
  );
};

export { LoggedOutLayout };
export type { LoggedOutLayoutProps };
