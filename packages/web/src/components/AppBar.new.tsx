import React from "react";
import { cn } from "@/lib/utils";

interface AppBarProps {
  title?: string;
  leftAction?: React.ReactNode;
  rightAction?: React.ReactNode;
  className?: string;
}

const AppBar: React.FC<AppBarProps> = ({
  title,
  leftAction,
  rightAction,
  className,
}) => {
  return (
    <header
      className={cn(
        "flex h-14 items-center justify-between border-b bg-background px-4",
        className
      )}
    >
      <div className="flex items-center gap-2">
        {leftAction}
        {title && (
          <h1 className="text-[18.8px] font-bold leading-[22px]">{title}</h1>
        )}
      </div>

      {rightAction}
    </header>
  );
};

export { AppBar };
export type { AppBarProps };
