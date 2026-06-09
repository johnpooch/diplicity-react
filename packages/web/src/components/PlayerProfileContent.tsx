import React from "react";
import { ShieldCheck, Sprout } from "lucide-react";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { ScreenCard, ScreenCardContent } from "@/components/ui/screen-card";
import { useUsersRetrieveSuspense } from "@/api/generated/endpoints";

interface PlayerProfileContentProps {
  userId: number;
}

const formatPercent = (rate: number) => `${Math.round(rate * 100)}%`;

const StatRow: React.FC<{ label: string; value: string | number }> = ({
  label,
  value,
}) => (
  <div className="flex items-center justify-between py-2">
    <span className="text-sm text-muted-foreground">{label}</span>
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
            <StatRow label="NMR Rate" value={formatPercent(profile.nmrRate)} />
            <StatRow label="CD Rate" value={formatPercent(profile.cdRate)} />
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
