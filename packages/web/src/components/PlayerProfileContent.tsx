import React from "react";
import { Info } from "lucide-react";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Card, CardContent } from "@/components/ui/card";
import { CommitmentBadge } from "@/components/CommitmentBadge";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Skeleton } from "@/components/ui/skeleton";
import { useUsersRetrieveSuspense } from "@/api/generated/endpoints";

interface PlayerProfileContentProps {
  userId: number;
}

const formatPercent = (rate: number) => `${Math.round(rate * 100)}%`;

interface SectionProps {
  title: string;
  children: React.ReactNode;
}

const Section: React.FC<SectionProps> = ({ title, children }) => (
  <section className="flex flex-col gap-2">
    <h2 className="text-sm font-medium text-muted-foreground">{title}</h2>
    <Card className="overflow-hidden py-0">
      <CardContent className="flex flex-col divide-y p-0">
        {children}
      </CardContent>
    </Card>
  </section>
);

interface StatRowProps {
  label: string;
  value: React.ReactNode;
  info?: string;
}

const StatRow: React.FC<StatRowProps> = ({ label, value, info }) => (
  <div className="flex items-center justify-between gap-4 px-6 py-3">
    <span className="flex items-center gap-1 text-sm">
      {label}
      {info && (
        <Popover>
          <PopoverTrigger asChild>
            <button
              type="button"
              className="-m-2 p-2 text-muted-foreground/60 hover:text-muted-foreground"
              aria-label={`What is ${label}?`}
            >
              <Info className="size-3.5" />
            </button>
          </PopoverTrigger>
          <PopoverContent className="text-sm">{info}</PopoverContent>
        </Popover>
      )}
    </span>
    <span className="truncate text-sm text-muted-foreground">{value}</span>
  </div>
);

const gameStats = [
  { label: "Total games", key: "totalGames" },
  { label: "Solo wins", key: "soloWins" },
  { label: "Draws", key: "draws" },
  { label: "Losses", key: "losses" },
] as const;

export const PlayerProfileContentSkeleton: React.FC = () => (
  <div className="space-y-4">
    <div className="flex items-center gap-4">
      <Skeleton className="size-16 rounded-full" />
      <div className="space-y-2">
        <Skeleton className="h-6 w-32" />
        <Skeleton className="h-4 w-40" />
      </div>
    </div>
    <Section title="Commitment">
      <StatRow label="NMR rate" value={<Skeleton className="h-5 w-8" />} />
    </Section>
    <Section title="Games">
      {gameStats.map(({ label }) => (
        <StatRow
          key={label}
          label={label}
          value={<Skeleton className="h-5 w-6" />}
        />
      ))}
    </Section>
  </div>
);

export const PlayerProfileContent: React.FC<PlayerProfileContentProps> = ({
  userId,
}) => {
  const { data: profile } = useUsersRetrieveSuspense(userId);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <Avatar className="size-16">
          <AvatarImage src={profile.picture ?? undefined} />
          <AvatarFallback className="text-lg">
            {profile.name[0]?.toUpperCase()}
          </AvatarFallback>
        </Avatar>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="truncate text-lg font-semibold">
              {profile.name}
            </span>
            <CommitmentBadge commitment={profile.commitment} />
          </div>
          <p className="text-sm text-muted-foreground">
            Joined{" "}
            {new Date(profile.createdAt).toLocaleDateString(undefined, {
              year: "numeric",
              month: "long",
            })}
          </p>
        </div>
      </div>

      <Section title="Commitment">
        <StatRow
          label="NMR rate"
          value={formatPercent(profile.nmrRate)}
          info="The percentage of movement phases where this player submitted no orders, based on their last 10 games."
        />
      </Section>

      <Section title="Games">
        {gameStats.map(({ label, key }) => (
          <StatRow key={key} label={label} value={profile[key]} />
        ))}
      </Section>
    </div>
  );
};
