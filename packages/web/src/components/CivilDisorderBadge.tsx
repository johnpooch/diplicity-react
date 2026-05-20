import React from "react";
import { UserX } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface CivilDisorderBadgeProps {
  className?: string;
}

export const CivilDisorderBadge: React.FC<CivilDisorderBadgeProps> = ({
  className,
}) => (
  <Badge variant="secondary" className={cn("gap-1", className)}>
    <UserX className="size-3" />
    Civil Disorder
  </Badge>
);
