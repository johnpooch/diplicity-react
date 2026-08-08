import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarInset,
  SidebarProvider,
} from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { Navigation } from "@/components/Navigation";
import { StaticMap } from "@/components/StaticMap";
import { cn } from "@/lib/utils";
import { ArrowLeft, Gavel, Map, MessageCircle } from "lucide-react";

const navigationItems = [
  { label: "Map", icon: Map },
  { label: "Orders", icon: Gavel },
  { label: "Chat", icon: MessageCircle },
];

interface GameShellProps {
  children: React.ReactNode;
  title: string;
  subtitle?: string;
  activeNavItem?: string;
  className?: string;
}

const GameShell: React.FC<GameShellProps> = ({
  children,
  title,
  subtitle,
  activeNavItem = "Chat",
  className,
}) => {
  const items = navigationItems.map(item => ({
    ...item,
    isActive: item.label === activeNavItem,
  }));

  return (
    <SidebarProvider>
      <div
        className={cn("flex h-dvh w-full flex-col overflow-hidden", className)}
      >
        <div className="flex min-h-0 w-full flex-1 items-stretch">
          <Sidebar>
            <SidebarHeader>
              <div className="flex items-center gap-2 px-1">
                <Button variant="ghost" size="icon" aria-label="Back">
                  <ArrowLeft />
                </Button>
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold">{title}</p>
                  {subtitle && (
                    <p className="truncate text-xs text-muted-foreground">
                      {subtitle}
                    </p>
                  )}
                </div>
              </div>
            </SidebarHeader>
            <SidebarContent>
              <div className="p-2">
                <div className="overflow-hidden rounded-md border bg-muted">
                  <StaticMap />
                </div>
              </div>
            </SidebarContent>
          </Sidebar>

          <SidebarInset className="flex min-w-0 flex-1 flex-col">
            {children}
          </SidebarInset>
        </div>

        <div className="block border-t bg-background md:hidden">
          <Navigation items={items} variant="bottom" />
        </div>
      </div>
    </SidebarProvider>
  );
};

export { GameShell };
