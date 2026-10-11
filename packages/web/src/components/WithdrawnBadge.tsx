import React from "react";
import { LogOut } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface WithdrawnBadgeProps {
  className?: string;
}

export const WithdrawnBadge: React.FC<WithdrawnBadgeProps> = ({
  className,
}) => (
  <Badge variant="secondary" className={cn("gap-1", className)}>
    <LogOut className="size-3" />
    Withdrawn
  </Badge>
);
