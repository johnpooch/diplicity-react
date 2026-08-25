import React from "react";
import { Plus, Vote } from "lucide-react";

import { NationFlag } from "@/components/NationFlag";
import { Nation } from "@/api/generated/endpoints";
import { cn } from "@/lib/utils";

type NationSeatState = "unset" | "ranked" | "assigned";

interface NationSeatProps {
  nations: readonly Nation[];
  nation: string | null | undefined;
  preferenceIds: readonly string[] | undefined;
  className?: string;
}

interface NationSeatFlagProps extends NationSeatProps {
  size?: "sm" | "lg";
}

interface NationSeatPillProps extends NationSeatProps {
  onClick?: () => void;
}

const getNationSeatState = (
  nation: string | null | undefined,
  preferenceIds: readonly string[] | undefined
): NationSeatState => {
  if (nation) return "assigned";
  return (preferenceIds?.length ?? 0) > 0 ? "ranked" : "unset";
};

const getNationSeatLabel = (
  nation: string | null | undefined,
  preferenceIds: readonly string[] | undefined
): string => {
  const state = getNationSeatState(nation, preferenceIds);
  if (state === "assigned") return nation as string;
  if (state === "ranked") return "Nation preferences provided";
  return "Choose nation preferences";
};

const findNationById = (nations: readonly Nation[], nationId: string | undefined) =>
  nationId ? nations.find(n => n.nationId === nationId) : undefined;

const findNationByName = (nations: readonly Nation[], name: string | null | undefined) =>
  name ? nations.find(n => n.name === name) : undefined;

const NationSeatFlag: React.FC<NationSeatFlagProps> = ({
  nations,
  nation,
  preferenceIds,
  size = "lg",
  className,
}) => {
  const state = getNationSeatState(nation, preferenceIds);
  const shown =
    state === "assigned"
      ? findNationByName(nations, nation)
      : findNationById(nations, preferenceIds?.[0]);
  const sizeClass = size === "sm" ? "size-4" : "size-8";

  const flag = shown ? (
    shown.flagUrl ? (
      <NationFlag
        flagUrl={shown.flagUrl}
        alt={shown.name}
        className={sizeClass}
        color={shown.color}
      />
    ) : (
      <span
        className={cn("rounded-full", sizeClass)}
        style={{ backgroundColor: shown.color }}
        aria-label={shown.name}
      />
    )
  ) : (
    <span
      className={cn(
        "flex items-center justify-center rounded-full bg-muted text-muted-foreground",
        sizeClass
      )}
    >
      <Plus className={size === "sm" ? "size-3" : "size-4"} />
    </span>
  );

  if (state !== "ranked" || size === "sm") {
    return <span className={cn("shrink-0", className)}>{flag}</span>;
  }

  return (
    <span className={cn("relative shrink-0", sizeClass, className)}>
      {flag}
      <span className="absolute -bottom-1 -right-1 flex size-4 items-center justify-center rounded-full bg-primary text-primary-foreground ring-2 ring-background">
        <Vote className="size-2.5" />
      </span>
    </span>
  );
};

const NationSeatPill: React.FC<NationSeatPillProps> = ({
  nations,
  nation,
  preferenceIds,
  className,
  onClick,
}) => {
  const state = getNationSeatState(nation, preferenceIds);
  const topChoice = findNationById(nations, preferenceIds?.[0]);
  const otherChoices = Math.max(0, (preferenceIds?.length ?? 0) - 1);
  const label =
    state === "assigned"
      ? (nation as string)
      : state === "ranked"
      ? [topChoice?.name ?? "Preferences", otherChoices > 0 && `+${otherChoices}`]
          .filter(Boolean)
          .join(" ")
      : "Choose nation";

  const content = (
    <>
      <NationSeatFlag
        nations={nations}
        nation={nation}
        preferenceIds={preferenceIds}
        size="sm"
      />
      <span className="truncate text-xs font-medium">{label}</span>
    </>
  );

  const chrome = cn(
    "flex max-w-[calc(100%-1rem)] items-center gap-1.5 rounded-full border px-2 py-1",
    state === "assigned" ? "bg-background" : "bg-background/70 backdrop-blur-sm",
    className
  );

  if (!onClick) {
    return (
      <div
        className={cn("pointer-events-none", chrome)}
        style={{ borderColor: findNationByName(nations, nation)?.color }}
      >
        {content}
      </div>
    );
  }

  return (
    <button
      onClick={onClick}
      className={cn(
        chrome,
        "cursor-pointer transition-colors hover:bg-background hover:shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        "after:absolute after:-inset-2.5 after:content-['']"
      )}
      style={{ borderColor: findNationByName(nations, nation)?.color }}
    >
      {content}
    </button>
  );
};

export { NationSeatFlag, NationSeatPill, getNationSeatState, getNationSeatLabel };
export type { NationSeatState };
