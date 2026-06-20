import React from "react";
import { Info, ShieldCheck, Sprout } from "lucide-react";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { ScreenCard, ScreenCardContent } from "@/components/ui/screen-card";
import { useUsersRetrieveSuspense } from "@/api/generated/endpoints";

interface PlayerProfileContentProps {
  userId: number;
}

const formatPercent = (rate: number) => `${Math.round(rate * 100)}%`;

interface StatRowProps {
  label: string;
  value: string | number;
  info?: string;
}

const StatRow: React.FC<StatRowProps> = ({ label, value, info }) => (
  <div className="flex items-center justify-between py-2">
    <span className="text-sm text-muted-foreground flex items-center gap-1">
      {label}
      {info && (
        <Popover>
          <PopoverTrigger asChild>
            <button
              type="button"
              className="text-muted-foreground/60 hover:text-muted-foreground"
              aria-label={`What is ${label}?`}
            >
              <Info className="size-3.5" />
            </button>
          </PopoverTrigger>
          <PopoverContent className="text-sm">{info}</PopoverContent>
        </Popover>
      )}
    </span>
    <span className="text-sm font-medium">{value}</span>
  </div>
);

export const PlayerProfileContent: React.FC<PlayerProfileContentProps> = ({
  userId,
}) => {
  const { data: profile } = useUsersRetrieveSuspense(userId);

  return (
    <div className="space-y-4">
      <ScreenCard>
        <ScreenCardContent>
          <div className="flex items-center gap-4">
            <Avatar className="size-16">
              <AvatarImage src={profile.picture ?? undefined} />
              <AvatarFallback className="text-lg">
                {profile.name[0]?.toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-lg font-semibold">{profile.name}</span>
                {profile.reliabilityTier === "reliable" && (
                  <Badge className="gap-1 bg-green-600">
                    <ShieldCheck className="size-3" />
                    Reliable
                  </Badge>
                )}
                {profile.reliabilityTier === "new" && (
                  <Badge variant="secondary" className="gap-1">
                    <Sprout className="size-3" />
                    New
                  </Badge>
                )}
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
        </ScreenCardContent>
      </ScreenCard>

      <ScreenCard>
        <ScreenCardContent>
          <h3 className="text-sm font-semibold mb-2">Reliability</h3>
          <div className="divide-y">
            <StatRow
              label="NMR Rate"
              value={formatPercent(profile.nmrRate)}
              info="The percentage of movement phases where this player submitted no orders, based on their last 10 games."
            />
          </div>
        </ScreenCardContent>
      </ScreenCard>

      <ScreenCard>
        <ScreenCardContent>
          <h3 className="text-sm font-semibold mb-2">Games</h3>
          <div className="divide-y">
            <StatRow label="Total Games" value={profile.totalGames} />
            <StatRow label="Solo Wins" value={profile.soloWins} />
            <StatRow label="Draws" value={profile.draws} />
            <StatRow label="Losses" value={profile.losses} />
          </div>
        </ScreenCardContent>
      </ScreenCard>
    </div>
  );
};
