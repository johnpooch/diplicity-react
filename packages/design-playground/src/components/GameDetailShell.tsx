import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarInset,
  SidebarProvider,
} from "@/components/ui/sidebar";
import { DiplicityLogo } from "@/components/DiplicityLogo";
import { Navigation } from "@/components/Navigation";
import { StaticMap } from "@/components/StaticMap";
import { cn } from "@/lib/utils";
import {
  ArrowLeft,
  Gavel,
  Info,
  Map,
  MessageCircle,
  Trophy,
  Users,
} from "lucide-react";

const navigationItems = [
  { label: "Map", icon: Map },
  { label: "Orders", icon: Gavel },
  { label: "Chat", icon: MessageCircle },
  { label: "Players", icon: Users },
  { label: "Info", icon: Info },
];

interface GameDetailShellProps {
  children: React.ReactNode;
  title: string;
  subtitle?: string;
  headerAction?: React.ReactNode;
  activeNavItem?: string;
  finished?: boolean;
  chatUnread?: boolean;
  ordersAttention?: boolean;
  mode?: "primary" | "secondary";
  backTo?: string;
  footer?: React.ReactNode;
  className?: string;
}

const GameDetailShell: React.FC<GameDetailShellProps> = ({
  children,
  title,
  subtitle,
  headerAction,
  activeNavItem = "Info",
  finished = false,
  chatUnread = false,
  ordersAttention = false,
  mode = "primary",
  backTo = "/my-games/single-list",
  footer,
  className,
}) => {
  const isSecondary = mode === "secondary";
  const items = navigationItems.map(item => ({
    ...item,
    icon: item.label === "Players" && finished ? Trophy : item.icon,
    isActive: item.label === activeNavItem,
    badge:
      item.label === "Chat" && chatUnread
        ? "unread"
        : item.label === "Orders" && ordersAttention
          ? "action required"
          : undefined,
  }));
  const sidebarItems = items.filter(item => item.label !== "Map");

  return (
    <SidebarProvider>
      <div
        className={cn("flex h-dvh w-full flex-col overflow-hidden", className)}
      >
        <div className="flex min-h-0 w-full flex-1 items-stretch">
          <Sidebar
            collapsible="none"
            className="hidden w-[72px] px-3 py-6 md:flex"
          >
            <SidebarHeader className="p-0">
              <Link
                to="/my-games/single-list"
                aria-label="Home"
                className="flex w-full justify-center"
              >
                <DiplicityLogo />
              </Link>
            </SidebarHeader>
            <SidebarContent className="justify-center">
              <Navigation
                items={sidebarItems}
                variant="compact"
                className="w-full p-0"
              />
            </SidebarContent>
            <SidebarFooter className="p-0">
              <div className="size-8" />
            </SidebarFooter>
          </Sidebar>

          <SidebarInset className="flex min-h-0 min-w-0 flex-col bg-sidebar md:w-[400px] md:flex-none">
            <div
              className={cn(
                "flex min-h-14 items-center gap-3 px-2",
                isSecondary ? "md:px-3" : "md:hidden"
              )}
            >
              {isSecondary ? (
                <Button
                  variant="outline"
                  size="icon-sm"
                  className="rounded-full"
                  asChild
                >
                  <Link to={backTo} aria-label="Back">
                    <ArrowLeft />
                  </Link>
                </Button>
              ) : (
                <Link to="/my-games/single-list" aria-label="Home">
                  <DiplicityLogo />
                </Link>
              )}
              <div className="min-w-0 flex-1">
                <p
                  className={cn(
                    "truncate font-semibold leading-tight",
                    isSecondary && "md:text-xl md:leading-9"
                  )}
                >
                  {title}
                </p>
                {subtitle && (
                  <p className="truncate text-xs text-muted-foreground leading-tight">
                    {subtitle}
                  </p>
                )}
              </div>
              {headerAction}
            </div>
            <div className="@container flex-1 overflow-y-auto">
              <div className="px-2 py-2 md:px-3 md:py-4">{children}</div>
            </div>
            {footer}
          </SidebarInset>

          <div className="hidden flex-1 overflow-hidden border-l bg-muted md:flex">
            <StaticMap className="h-full w-full object-cover" />
          </div>
        </div>

        {!isSecondary && (
          <div className="block border-t bg-background md:hidden">
            <Navigation items={items} variant="bottom" />
          </div>
        )}
      </div>
    </SidebarProvider>
  );
};

export { GameDetailShell };
