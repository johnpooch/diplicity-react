import React from "react";
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

interface HomeLayoutProps {
  /**
   * Content for the left sidebar (e.g., navigation)
   **/
  left: React.ReactNode;
  /**
   * Main content area
   **/
  center: React.ReactNode;
  /**
   * Content for the right sidebar (e.g., info panel)
   **/
  right: React.ReactNode;
  /**
   * Content for the bottom navigation (mobile only)
   **/
  bottom: React.ReactNode;
  /**
   * Custom className for the root container
   **/
  className?: string;
}

/**
 * HomeLayout - A responsive app shell component
 *
 * Provides a three-column layout (left, center, right) with optional bottom navigation.
 * Uses ShadCN Sidebar for the left sidebar with collapsible functionality.
 *
 * Responsive behavior:
 * - Mobile: Sidebar hidden (trigger button shown) + center + bottom nav
 * - Tablet/Desktop: Collapsible sidebar (icon mode) + center + right (desktop only)
 *
 * @example
 * ```tsx
 * <HomeLayout
 *   left={<Navigation />}
 *   center={<MainContent />}
 *   right={<InfoPanel />}
 *   bottom={<MobileNav />}
 * />
 * ```
 */
const HomeLayout: React.FC<HomeLayoutProps> = ({
  left,
  center,
  right,
  bottom,
  className,
}) => {
  // Bottom navigation: visible on mobile only
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
            <SidebarContent>{left}</SidebarContent>
          </Sidebar>

          {/* Main Content Area */}
          <SidebarInset className="flex min-w-0 flex-1 flex-col">
            {/* Mobile menu trigger */}
            <div className="md:hidden p-2 border-b shrink-0">
              <SidebarTrigger />
            </div>

            {/* Center content - scrollable */}
            <div className="flex-1 overflow-y-auto">
              <div className="mx-auto w-full max-w-[672px] py-4">{center}</div>
            </div>
          </SidebarInset>

          {/* Right Sidebar - Styled to match left sidebar */}
          {right && (
            <div className="hidden xl:flex w-64 border-l flex-col">
              <div className="bg-sidebar flex h-full w-full flex-col p-2">
                {right}
              </div>
            </div>
          )}
        </div>

        {/* Bottom Navigation */}
        {bottom && <div className={bottomClasses}>{bottom}</div>}
      </div>
    </SidebarProvider>
  );
};

export { HomeLayout };
export type { HomeLayoutProps };
