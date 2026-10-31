import React, { useState } from "react";
import { cn } from "@/lib/utils";
import { Tooltip, TooltipContent, TooltipTrigger } from "./ui/tooltip";

interface LockedJoinTooltipProps {
  children: React.ReactNode;
  className?: string;
}

export const LockedJoinTooltip: React.FC<LockedJoinTooltipProps> = ({
  children,
  className,
}) => {
  const [open, setOpen] = useState(false);

  return (
    <Tooltip open={open} onOpenChange={setOpen}>
      <TooltipTrigger asChild>
        <span
          tabIndex={0}
          className={cn("inline-flex rounded-md", className)}
          onClick={event => {
            event.preventDefault();
            setOpen(true);
          }}
        >
          {children}
        </span>
      </TooltipTrigger>
      <TooltipContent>Your commitment is too low to join this game</TooltipContent>
    </Tooltip>
  );
};
