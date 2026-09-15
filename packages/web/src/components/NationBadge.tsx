import React from "react";
import { Badge } from "@/components/ui/badge";
import { findNationColor, getContrastColor } from "./NationFlag";

interface NationBadgeProps {
  nations: ReadonlyArray<{ name: string; color: string }>;
  nation: string | null | undefined;
  children?: React.ReactNode;
}

const NationBadge: React.FC<NationBadgeProps> = ({ nations, nation, children }) => {
  if (!nation) return null;
  const color = findNationColor(nations, nation);
  return (
    <Badge
      className="max-w-32 truncate"
      style={{ backgroundColor: color ?? undefined, color: getContrastColor(color) }}
    >
      {children ?? nation}
    </Badge>
  );
};

export { NationBadge };
