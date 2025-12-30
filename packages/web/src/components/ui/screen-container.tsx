import * as React from "react"
import { cn } from "@/lib/utils"

interface ScreenContainerProps {
  children: React.ReactNode;
  className?: string;
}

function ScreenContainer({ children, className }: ScreenContainerProps) {
  return (
    <div className={cn("w-full space-y-4", className)}>
      {children}
    </div>
  );
}

export { ScreenContainer }
