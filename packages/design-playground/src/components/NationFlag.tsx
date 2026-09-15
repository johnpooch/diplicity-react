import { createContext, useContext, type ReactNode } from "react";
import { cn } from "@/lib/utils";

const nationHex: Record<string, string> = {
  Austria: "#F44336",
  England: "#2196F3",
  France: "#80DEEA",
  Germany: "#90A4AE",
  Italy: "#4CAF50",
  Russia: "#F5F5F5",
  Turkey: "#FFC107",
};

const flagSrc: Record<string, string> = {
  Austria: "/flags/austria.svg",
  England: "/flags/england.svg",
  France: "/flags/france.svg",
  Germany: "/flags/germany.svg",
  Italy: "/flags/italy.svg",
  Russia: "/flags/russia.svg",
  Turkey: "/flags/turkey.svg",
};

const DEFAULT_NATION_COLOR = "#808080";

const NationFlagsContext = createContext(true);

const NationFlagsProvider = ({
  enabled,
  children,
}: {
  enabled: boolean;
  children: ReactNode;
}) => {
  return (
    <NationFlagsContext value={enabled}>{children}</NationFlagsContext>
  );
};

const findNationColor = (nation: string): string =>
  nationHex[nation] ?? DEFAULT_NATION_COLOR;

const toHex6 = (color: string): string => {
  const short = /^#([0-9a-fA-F])([0-9a-fA-F])([0-9a-fA-F])$/.exec(color);
  if (short) {
    return `#${short[1]}${short[1]}${short[2]}${short[2]}${short[3]}${short[3]}`;
  }
  if (/^#[0-9a-fA-F]{6}$/.test(color)) return color;
  return DEFAULT_NATION_COLOR;
};

const brightnessByColor = (hex: string): number => {
  const match = /^#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})$/.exec(
    toHex6(hex)
  );
  if (!match) return 128;
  const r = parseInt(match[1], 16);
  const g = parseInt(match[2], 16);
  const b = parseInt(match[3], 16);
  return (r * 299 + g * 587 + b * 114) / 1000;
};

const mixTowardBlack = (hex: string, amount: number): string => {
  const match = /^#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})$/.exec(
    toHex6(hex)
  );
  if (!match) return hex;
  const mix = (channel: string) =>
    Math.round(parseInt(channel, 16) * (1 - amount))
      .toString(16)
      .padStart(2, "0");
  return `#${mix(match[1])}${mix(match[2])}${mix(match[3])}`;
};

const ringColor = (hex: string): string =>
  brightnessByColor(hex) > 186 ? mixTowardBlack(hex, 0.28) : hex;

const contrastColor = (hex: string): string =>
  brightnessByColor(hex) > 128 ? "#111111" : "#ffffff";

const sizeClass = {
  sm: "size-5",
  md: "size-8",
  lg: "size-12",
} as const;

const monogramClass = {
  sm: "text-[0px]",
  md: "text-[10px]",
  lg: "text-sm",
} as const;

type NationFlagSize = keyof typeof sizeClass;

interface NationFlagProps {
  nation: string;
  size?: NationFlagSize;
  preferred?: boolean;
  className?: string;
}

const NationFlag: React.FC<NationFlagProps> = ({
  nation,
  size = "md",
  preferred = false,
  className,
}) => {
  const flagsEnabled = useContext(NationFlagsContext);
  const color = findNationColor(nation);
  const src = flagsEnabled ? flagSrc[nation] : undefined;
  const ringPx = src ? 1 : size === "lg" ? 3 : 2;
  const showMonogram = !src && size !== "sm";

  return (
    <span
      aria-hidden
      className={cn(
        "box-border inline-flex shrink-0 items-center justify-center overflow-hidden rounded-full font-semibold",
        preferred ? "border-dashed" : "border-solid",
        sizeClass[size],
        monogramClass[size],
        className
      )}
      style={{
        borderWidth: preferred ? 2 : ringPx,
        borderColor: ringColor(color),
        backgroundColor: src ? undefined : color,
        color: contrastColor(color),
      }}
    >
      {src ? (
        <img src={src} alt="" className="size-full object-cover" />
      ) : showMonogram ? (
        nation.slice(0, 2).toUpperCase()
      ) : null}
    </span>
  );
};

export {
  NationFlag,
  NationFlagsProvider,
  findNationColor,
  toHex6,
  brightnessByColor,
};
