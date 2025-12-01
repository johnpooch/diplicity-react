import React from "react";
import { cn } from "@/lib/utils"; // ShadCN utility for class merging

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
 *
 * Responsive behavior:
 * - Mobile: Center only + bottom nav
 * - Tablet: Left (collapsed) + center
 * - Desktop: Left (expanded) + center + right
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
  // Left sidebar: hidden on mobile, visible on tablet+
  const leftClasses = cn("border-r", "hidden md:block");

  // Right sidebar: hidden on mobile and tablet, visible on desktop only
  const rightClasses = cn("border-l", "hidden lg:block", "lg:w-[240px]");

  // Bottom navigation: visible on mobile only
  const bottomClasses = cn("border-t bg-background", "block md:hidden");

  return (
    <div className={cn("flex flex-col h-screen w-full", className)}>
      {/* Main content area */}
      <div className="flex flex-1 min-h-0 w-full">
        {/* Main container with max-width constraint */}
        <div className="flex w-full max-w-[1200px] flex-1 mx-auto">
          {/* Left Sidebar */}
          <div className={leftClasses}>{left}</div>

          {/* Center Panel */}
          <div className="flex min-w-0 flex-1 flex-col w-full">
            {/* Main Content */}
            <div className="flex-1 w-full overflow-auto">{center}</div>
          </div>

          {/* Right Sidebar */}
          <div className={rightClasses}>{right}</div>
        </div>
      </div>

      {/* Bottom Navigation */}
      {bottom && <div className={bottomClasses}>{bottom}</div>}
    </div>
  );
};

export { HomeLayout };
export type { HomeLayoutProps };
