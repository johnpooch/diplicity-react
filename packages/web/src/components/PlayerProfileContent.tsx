import React from "react";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { CommitmentBadge } from "@/components/CommitmentBadge";
import { InfoButton } from "@/components/InfoButton";
import { NationFlag } from "@/components/NationFlag";
import { useUsersRetrieveSuspense, type OutcomeEnum } from "@/api/generated/endpoints";

interface PlayerProfileContentProps {
  userId: number;
}

const formatPercent = (rate: number) => `${Math.round(rate * 100)}%`;

const outcomeLabel: Record<OutcomeEnum, string> = {
  won: "Won",
  drew: "Drew",
  eliminated: "Eliminated",
  survived: "Survived",
};

const outcomeVariant: Record<OutcomeEnum, "default" | "secondary" | "outline"> = {
  won: "default",
  drew: "secondary",
  eliminated: "outline",
  survived: "outline",
};

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
    <>
      <Card>
        <CardContent className="flex flex-col gap-4">
          <div className="flex items-center gap-4">
            <Avatar className="size-16">
              <AvatarImage src={profile.picture ?? undefined} />
              <AvatarFallback className="text-xl">
                {profile.name[0]?.toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="truncate text-xl font-semibold">{profile.name}</h2>
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

          <Separator />

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
        </CardContent>
      </Card>

      {profile.favouriteNation && (
        <Card>
          <CardContent className="flex flex-col gap-3">
            <h2 className="font-semibold">Most played</h2>
            <div className="flex items-center gap-3">
              <NationFlag
                flagUrl={profile.favouriteNation.nation.flagUrl}
                color={profile.favouriteNation.nation.color}
                alt={profile.favouriteNation.nation.name}
                className="size-10"
              />
              <div>
                <p className="font-medium">{profile.favouriteNation.nation.name}</p>
                <p className="text-sm text-muted-foreground">
                  {profile.favouriteNation.gamesPlayed} of {profile.totalGames} games
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {profile.recentResults.length > 0 && (
        <Card>
          <CardContent className="flex flex-col gap-3">
            <h2 className="font-semibold">Recent results</h2>
            <div className="flex flex-col gap-3">
              {profile.recentResults.map(result => (
                <div key={result.gameId} className="flex items-center gap-3">
                  <NationFlag
                    flagUrl={result.nation.flagUrl}
                    color={result.nation.color}
                    alt={result.nation.name}
                    className="size-10"
                  />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{result.gameName}</p>
                    <p className="truncate text-sm text-muted-foreground">
                      {result.nation.name} ·{" "}
                      {new Date(result.finishedAt).toLocaleDateString(undefined, {
                        year: "numeric",
                        month: "short",
                        day: "numeric",
                      })}
                    </p>
                  </div>
                  <Badge variant={outcomeVariant[result.outcome]}>
                    {outcomeLabel[result.outcome]}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </>
  );
};
