import React from "react";
import { useLocation, useNavigate } from "react-router";
import { cn } from "@/lib/utils";
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { Item, ItemMedia, ItemContent, ItemTitle } from "@/components/ui/item";
import { DiplicityLogo } from "@/components/DiplicityLogo";
import { Navigation } from "@/components/Navigation";
import { InfoPanel } from "@/components/InfoPanel.new";
import { navigationItems } from "@/navigation/navigationItems";

interface HomeLayoutProps {
  /**
   * Main content area
   **/
  children: React.ReactNode;
  /**
   * Custom className for the root container
   **/
  className?: string;
}

/**
 * HomeLayout - A responsive app shell component
 *
 * Provides a three-column layout with navigation (left), main content (center),
 * and info panel (right), plus bottom navigation for mobile.
 * Uses ShadCN Sidebar for the left sidebar with collapsible functionality.
 *
 * Responsive behavior:
 * - Mobile: Sidebar hidden (trigger button shown) + center + bottom nav
 * - Tablet/Desktop: Collapsible sidebar (icon mode) + center + right (desktop only)
 *
 * @example
 * ```tsx
 * <HomeLayout>
 *   <MyGamesContent />
 * </HomeLayout>
 * ```
 */
const HomeLayout: React.FC<HomeLayoutProps> = ({ children, className }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = navigationItems.map(item => ({
    ...item,
    isActive: location.pathname === item.path,
  }));

  const bottomClasses = cn("border-t bg-background", "block md:hidden");

  return (
    <SidebarProvider>
      <div
        className={cn(
          "flex flex-col h-screen w-full overflow-hidden",
          className
        )}
      >
        <div className="flex items-stretch flex-1 min-h-0 w-full">
          {/* Left Sidebar - ShadCN Sidebar with collapsible functionality */}
          <Sidebar collapsible="icon">
            <SidebarHeader>
              <Item className="p-1">
                <ItemMedia variant="image">
                  <DiplicityLogo />
                </ItemMedia>
                <ItemContent>
                  <ItemTitle>Diplicity</ItemTitle>
                </ItemContent>
              </Item>
            </SidebarHeader>
            <SidebarContent>
              <Navigation
                items={navItems}
                variant="sidebar"
                onItemClick={path => navigate(path)}
              />
            </SidebarContent>
          </Sidebar>

          {/* Main Content Area */}
          <SidebarInset className="flex min-w-0 flex-1 flex-col">
            {/* Center content - scrollable */}
            <div className="flex-1 overflow-y-auto">
              <div className="mx-auto w-full max-w-[672px] py-4 px-2">
                {children}
              </div>
            </div>
          </SidebarInset>

          {/* Right Sidebar - Info Panel */}
          <div className="hidden xl:flex w-64 border-l flex-col">
            <div className="bg-sidebar flex h-full w-full flex-col p-2">
              <InfoPanel />
            </div>
          </div>
        </div>

        {/* Bottom Navigation */}
        <div className={bottomClasses}>
          <Navigation
            items={navItems}
            variant="bottom"
            onItemClick={path => navigate(path)}
          />
        </div>
      </div>
    </SidebarProvider>
  );
};

export { HomeLayout };
export type { HomeLayoutProps };
