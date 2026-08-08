import { cn } from "@/lib/utils";
import { type LucideIcon } from "lucide-react";

export interface NavigationItemType {
  label: string;
  icon: LucideIcon;
  isActive?: boolean;
  badge?: string;
}

interface NavigationProps {
  items: NavigationItemType[];
  variant: "sidebar" | "bottom";
  className?: string;
}

const Navigation: React.FC<NavigationProps> = ({
  items,
  variant,
  className,
}) => {
  const containerClasses = cn(
    "flex",
    variant === "bottom"
      ? "h-14 flex-row items-center justify-around px-2"
      : "w-60 flex-col gap-1 p-2",
    className
  );

  return (
    <nav className={containerClasses} aria-label="Main navigation">
      {items.map(item => {
        const Icon = item.icon;
        const isActive = item.isActive ?? false;

        return (
          <button
            key={item.label}
            type="button"
            aria-current={isActive ? "page" : undefined}
            className={cn(
              "flex items-center transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              variant === "sidebar" &&
                cn(
                  "w-full gap-3 rounded-lg px-3 py-2",
                  isActive
                    ? "bg-sidebar-accent text-sidebar-accent-foreground"
                    : "text-sidebar-foreground hover:bg-sidebar-accent/50"
                ),
              variant === "bottom" &&
                cn(
                  "flex-col items-center justify-center gap-0.5 px-3 py-1",
                  isActive
                    ? "text-primary"
                    : "text-muted-foreground hover:text-foreground"
                )
            )}
          >
            <div className="relative">
              <Icon
                className="size-5"
                strokeWidth={isActive ? 2.5 : 1.5}
              />
              {variant === "bottom" && item.badge && (
                <span className="absolute -right-1 -top-1 size-2 rounded-full bg-primary" />
              )}
            </div>
            {variant === "sidebar" && (
              <>
                <span className="text-sm font-medium">{item.label}</span>
                {item.badge && (
                  <span className="rounded-full bg-primary px-1.5 py-0.5 text-[10px] font-medium text-primary-foreground">
                    {item.badge}
                  </span>
                )}
              </>
            )}
            {variant === "bottom" && (
              <span className="text-[10px] font-medium">{item.label}</span>
            )}
          </button>
        );
      })}
    </nav>
  );
};

export { Navigation };
