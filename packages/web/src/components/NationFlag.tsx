import React from "react";
import { cn } from "../lib/utils";

interface NationFlagProps {
  flagUrl: string | null | undefined;
  alt?: string;
  size?: "sm" | "md" | "lg";
  color?: string | null;
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
  color,
  className,
  style,
}) => {
  if (flagUrl) {
    return (
      <img
        src={flagUrl}
        alt={alt ?? ""}
        className={cn("rounded-full object-cover", sizeClasses[size], className)}
        style={color ? { boxShadow: `0 0 0 1px ${color}`, ...style } : style}
      />
    );
  }

  if (!alt) return null;

  return (
    <span
      aria-label={alt}
      className={cn(
        "flex items-center justify-center rounded-full text-[8px] font-semibold leading-none",
        sizeClasses[size],
        className
      )}
      style={{
        backgroundColor: color ?? undefined,
        color: getContrastColor(color),
        ...style,
      }}
    >
      {alt.slice(0, 2).toUpperCase()}
    </span>
  );
};

const getContrastColor = (hexColor: string | null | undefined): string => {
  if (!hexColor) return "#ffffff";
  const hex = hexColor.replace("#", "");
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return luminance > 0.5 ? "#000000" : "#ffffff";
};

const findNationFlagUrl = (
  nations: ReadonlyArray<{ name: string; flagUrl: string | null }>,
  nationName: string | null | undefined
): string | null => {
  if (!nationName) return null;
  return nations.find((n) => n.name === nationName)?.flagUrl ?? null;
};

const findNationColor = (
  nations: ReadonlyArray<{ name: string; color: string }>,
  nationName: string | null | undefined
): string | null => {
  if (!nationName) return null;
  return nations.find((n) => n.name === nationName)?.color ?? null;
};

export { NationFlag, findNationFlagUrl, findNationColor, getContrastColor };
