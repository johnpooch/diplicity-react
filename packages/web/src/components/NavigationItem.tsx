import React from "react";
import { cn } from "@/lib/utils"; // Assuming this is needed for combining classes
import { Button } from "@/components/ui/button";
import { Icon, IconName } from "./Icon";

interface NavigationItemProps {
  label: string;
  icon: IconName;
  isActive: boolean;
  onClick: () => void;
  variant: "sidebar" | "compact" | "bottom";
  className?: string;
}

const NavigationItem: React.FC<NavigationItemProps> = ({
  label,
  icon,
  isActive,
  onClick,
  variant,
  className,
}) => {
  const showLabel = variant === "sidebar";
  const iconSize = variant === "bottom" ? 24 : 20;

  const buttonLayoutClasses = cn(
    "flex items-center gap-3 h-auto p-0",
    variant === "sidebar" && "w-full justify-start px-3 py-2",
    variant === "compact" && "w-10 h-10 p-2 justify-center",
    variant === "bottom" && "min-w-[44px] min-h-[44px] flex-col gap-1 p-1",
    className
  );

  const sidebarTextClasses = cn("text-sm", isActive && "font-semibold");

  return (
    <Button
      onClick={onClick}
      variant="ghost"
      className={buttonLayoutClasses}
      aria-current={isActive ? "page" : undefined}
      aria-label={!showLabel ? label : undefined}
    >
      <Icon name={icon} size={iconSize} highlight={isActive} variant="lucide" />
      {showLabel && <span className={sidebarTextClasses}>{label}</span>}
    </Button>
  );
};

export { NavigationItem };
export type { NavigationItemProps };
