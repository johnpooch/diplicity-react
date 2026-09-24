import React from "react";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { CommitmentBadge } from "@/components/CommitmentBadge";
import { InfoButton } from "@/components/InfoButton";
import { ScreenCard, ScreenCardContent } from "@/components/ui/screen-card";
import { useUsersRetrieveSuspense } from "@/api/generated/endpoints";

interface PlayerProfileContentProps {
  userId: number;
}

const formatPercent = (rate: number) => `${Math.round(rate * 100)}%`;

interface StatTileProps {
  label: string;
  value: string | number;
  hint?: string;
  info?: string;
}

const StatTile: React.FC<StatTileProps> = ({ label, value, hint, info }) => (
  <div>
    <p className="text-2xl font-semibold tabular-nums">{value}</p>
    <span className="flex items-center gap-1 text-sm text-muted-foreground">
      {label}
      {info && <InfoButton label={label} text={info} />}
    </span>
    {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
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
        </ScreenCardContent>
      </ScreenCard>

      <ScreenCard>
        <ScreenCardContent>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <StatTile label="Games" value={profile.totalGames} />
            <StatTile
              label="Victory"
              value={profile.soloWins}
              hint={
                profile.totalGames > 0
                  ? `${formatPercent(profile.soloWins / profile.totalGames)} of games`
                  : undefined
              }
            />
            <StatTile label="Draws" value={profile.draws} />
            <StatTile
              label="Reliability"
              value={formatPercent(1 - profile.nmrRate)}
              info="How consistently this player submits orders, based on their last 10 rated phases."
            />
          </div>
        </ScreenCardContent>
      </ScreenCard>
    </div>
  );
};
