import React from "react";
import { cn } from "../lib/utils";

interface NationFlagProps {
  flagUrl: string | null | undefined;
  alt?: string;
  size?: "sm" | "md" | "lg";
  className?: string;
  style?: React.CSSProperties;
}

const sizeClasses = {
  sm: "size-4",
  md: "size-5",
  lg: "size-6",
};

const NationFlag: React.FC<NationFlagProps> = ({
  flagUrl,
  alt,
  size = "md",
  className,
  style,
}) => {
  if (!flagUrl) return null;

  return (
    <img
      src={flagUrl}
      alt={alt ?? ""}
      className={cn("rounded-full object-cover", sizeClasses[size], className)}
      style={style}
    />
  );
};

const findNationFlagUrl = (
  nations: ReadonlyArray<{ name: string; flagUrl: string | null }>,
  nationName: string | null | undefined
): string | null => {
  if (!nationName) return null;
  return nations.find((n) => n.name === nationName)?.flagUrl ?? null;
};

export { NationFlag, findNationFlagUrl };
