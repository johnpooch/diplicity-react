import React from "react";
import { Badge } from "@/components/ui/badge";
import { findNationColor } from "./NationFlag";

const getContrastColor = (hexColor: string | null): string => {
  if (!hexColor) return "#ffffff";
  const hex = hexColor.replace("#", "");
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return luminance > 0.5 ? "#000000" : "#ffffff";
};

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
