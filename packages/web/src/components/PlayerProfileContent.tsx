import React from "react";
import { Info } from "lucide-react";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { CommitmentBadge, COMMITMENT_TIERS } from "@/components/CommitmentBadge";
import { NationFlag } from "@/components/NationFlag";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { ScreenCard, ScreenCardContent } from "@/components/ui/screen-card";
import {
  useUsersRetrieveSuspense,
  type OutcomeEnum,
} from "@/api/generated/endpoints";

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

const outcomeVariant: Record<
  OutcomeEnum,
  "default" | "secondary" | "outline"
> = {
  won: "default",
  drew: "secondary",
  eliminated: "outline",
  survived: "outline",
};

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
          <h3 className="text-sm font-semibold mb-2">Commitment</h3>
          <div className="divide-y">
            <StatRow
              label="Tier"
              value={COMMITMENT_TIERS[profile.commitment]?.label ?? profile.commitment}
              info={
                profile.commitment === "undefined"
                  ? "This player hasn't played enough rated phases to have a commitment rating yet. A rating appears after 10 rated phases."
                  : "How consistently this player submits orders, based on their last 10 rated phases."
              }
            />
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

      {profile.favouriteNation && (
        <ScreenCard>
          <ScreenCardContent>
            <h3 className="text-sm font-semibold mb-2">Most Played</h3>
            <div className="flex items-center gap-3">
              <NationFlag
                flagUrl={profile.favouriteNation.nation.flagUrl}
                color={profile.favouriteNation.nation.color}
                alt={profile.favouriteNation.nation.name}
                className="size-10"
              />
              <div>
                <p className="text-sm font-medium">
                  {profile.favouriteNation.nation.name}
                </p>
                <p className="text-sm text-muted-foreground">
                  {profile.favouriteNation.gamesPlayed} of {profile.totalGames}{" "}
                  games
                </p>
              </div>
            </div>
          </ScreenCardContent>
        </ScreenCard>
      )}

      {profile.recentResults.length > 0 && (
        <ScreenCard>
          <ScreenCardContent>
            <h3 className="text-sm font-semibold mb-2">Recent Results</h3>
            <div className="divide-y">
              {profile.recentResults.map(result => (
                <div
                  key={result.gameId}
                  className="flex items-center gap-3 py-2"
                >
                  <NationFlag
                    flagUrl={result.nation.flagUrl}
                    color={result.nation.color}
                    alt={result.nation.name}
                    className="size-10"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      {result.gameName}
                    </p>
                    <p className="text-sm text-muted-foreground truncate">
                      {result.nation.name} ·{" "}
                      {new Date(result.finishedAt).toLocaleDateString(
                        undefined,
                        {
                          year: "numeric",
                          month: "short",
                          day: "numeric",
                        }
                      )}
                    </p>
                  </div>
                  <Badge variant={outcomeVariant[result.outcome]}>
                    {outcomeLabel[result.outcome]}
                  </Badge>
                </div>
              ))}
            </div>
          </ScreenCardContent>
        </ScreenCard>
      )}
    </div>
  );
};
