import React from "react";
import { UserMinus } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface KickedBadgeProps {
  className?: string;
}

export const KickedBadge: React.FC<KickedBadgeProps> = ({ className }) => (
  <Badge variant="secondary" className={cn("gap-1", className)}>
    <UserMinus className="size-3" />
    Removed
  </Badge>
);
