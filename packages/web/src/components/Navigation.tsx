import React from "react";
import { cn } from "@/lib/utils";
import { type LucideIcon } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export interface NavigationItemType {
  label: string;
  icon: LucideIcon;
  path: string;
  isActive?: boolean;
  badge?: string;
}

interface NavigationProps {
  items: NavigationItemType[];
  variant: "sidebar" | "compact" | "bottom";
  onItemClick: (path: string) => void;
  className?: string;
}

interface NavigationItemProps {
  label: string;
  icon: LucideIcon;
  isActive: boolean;
  onClick: () => void;
  variant: "sidebar" | "compact" | "bottom";
  badge?: string;
}

const NavigationItem: React.FC<NavigationItemProps> = ({
  label,
  icon,
  isActive,
  onClick,
  variant,
  badge,
}) => {
  const baseClasses =
    "flex items-center cursor-pointer transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-ring";

  const variantClasses = {
    sidebar: cn(
      "w-full gap-3 rounded-lg px-3 py-2",
      isActive
        ? "bg-sidebar-accent text-sidebar-accent-foreground"
        : "text-sidebar-foreground hover:bg-sidebar-accent/50"
    ),
    compact: cn(
      "justify-center rounded-lg p-2",
      isActive
        ? "bg-sidebar-accent text-sidebar-accent-foreground"
        : "text-sidebar-foreground hover:bg-sidebar-accent/50"
    ),
    bottom: cn(
      "flex-col items-center justify-center gap-0.5 py-1 px-3",
      isActive
        ? "text-primary"
        : "text-muted-foreground hover:text-foreground"
    ),
  };

  const IconComponent = icon;

  const badgeElement = badge && (
    <span className="rounded-full bg-primary px-1.5 py-0.5 text-[10px] font-medium text-primary-foreground">
      {badge}
    </span>
  );

  const content = (
    <button
      onClick={onClick}
      className={cn(baseClasses, variantClasses[variant])}
      aria-current={isActive ? "page" : undefined}
    >
      <IconComponent className="size-5" strokeWidth={isActive ? 2.5 : 1.5} />
      {variant === "sidebar" && (
        <>
          <span className="text-sm font-medium">{label}</span>
          {badgeElement}
        </>
      )}
      {variant === "bottom" && (
        <span className="text-[10px] font-medium">{label}</span>
      )}
    </button>
  );

  if (variant === "compact") {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>{content}</TooltipTrigger>
          <TooltipContent side="right">{label}</TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  return content;
};

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
      {items.map(item => (
        <NavigationItem
          key={item.path}
          label={item.label}
          icon={item.icon}
          isActive={item.isActive || false}
          onClick={() => onItemClick(item.path)}
          variant={variant}
          badge={item.badge}
        />
      ))}
    </nav>
  );
};

export { Navigation };
export type { NavigationProps };
