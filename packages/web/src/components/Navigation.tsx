import React from "react";
import { cn } from "@/lib/utils";
import { NavigationItem } from "./NavigationItem";
import { IconName } from "./Icon";

export interface NavigationItemType {
  label: string;
  icon: IconName;
  path: string;
  isActive?: boolean;
}

interface NavigationProps {
  items: NavigationItemType[];
  variant: "sidebar" | "compact" | "bottom";
  onItemClick: (path: string) => void;
  className?: string;
}

const Navigation: React.FC<NavigationProps> = ({
  items,
  variant,
  onItemClick,
  className,
}) => {
  const containerClasses = cn(
    "flex",
    variant === "bottom"
      ? "flex-row items-center justify-around"
      : "flex-col gap-1",
    variant === "sidebar" && "w-60 p-2",
    variant === "compact" && "w-14 p-2 items-center",
    variant === "bottom" && "h-14 px-2",
    className
  );

  return (
    <nav className={containerClasses} aria-label="Main navigation">
      {items.map((item) => (
        <NavigationItem
          key={item.path}
          label={item.label}
          icon={item.icon}
          isActive={item.isActive || false}
          onClick={() => onItemClick(item.path)}
          variant={variant}
        />
      ))}
    </nav>
  );
};

export { Navigation };
export type { NavigationProps };
