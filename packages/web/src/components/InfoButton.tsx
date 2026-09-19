import React, { useState } from "react";
import { Info } from "lucide-react";

import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

interface InfoButtonProps {
  label: string;
  text: string;
  className?: string;
}

const InfoButton: React.FC<InfoButtonProps> = ({ label, text, className }) => {
  const [open, setOpen] = useState(false);

  return (
    <Tooltip open={open} onOpenChange={setOpen}>
      <TooltipTrigger asChild>
        <button
          type="button"
          onClick={e => {
            e.stopPropagation();
            setOpen(true);
          }}
          className={cn(
            "-m-2 p-2 text-muted-foreground/60 hover:text-muted-foreground",
            className
          )}
          aria-label={`What are ${label}?`}
        >
          <Info className="size-3.5" />
        </button>
      </TooltipTrigger>
      <TooltipContent>{text}</TooltipContent>
    </Tooltip>
  );
};

export { InfoButton };
