import React from "react";
import { Skull } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface EliminatedBadgeProps {
  className?: string;
}

export const EliminatedBadge: React.FC<EliminatedBadgeProps> = ({
  className,
}) => (
  <Badge variant="secondary" className={cn("gap-1", className)}>
    <Skull className="size-3" />
    Eliminated
  </Badge>
);
