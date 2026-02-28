import React from "react";
import { cn } from "@/lib/utils";

interface SafeAreaViewProps {
  children: React.ReactNode;
  className?: string;
}

const SafeAreaView: React.FC<SafeAreaViewProps> = ({ children, className }) => (
  <div
    className={cn(
      "pt-[var(--safe-area-top)] pb-[var(--safe-area-bottom)]",
      className
    )}
  >
    {children}
  </div>
);

export { SafeAreaView };
