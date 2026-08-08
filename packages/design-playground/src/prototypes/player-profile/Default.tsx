import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { ScreenContainer } from "@/components/ui/screen-container";
import { HomeShell } from "@/components/HomeShell";
import { ScreenHeader } from "@/components/ScreenHeader";
import { NationAvatar } from "@/components/NationAvatar";
import { profile } from "@/data/fixtures";

const outcomeVariant: Record<string, "default" | "secondary" | "outline"> = {
  Won: "default",
  Drew: "secondary",
  Eliminated: "outline",
  Resigned: "outline",
};

const PlayerProfile: React.FC = () => {
  return (
    <HomeShell activeNavItem="My Games">
      <ScreenContainer>
        <ScreenHeader title="Profile" />

        <Card>
          <CardContent className="flex flex-col gap-4">
            <div className="flex items-center gap-4">
              <Avatar className="size-16">
                <AvatarFallback className="text-xl">O</AvatarFallback>
              </Avatar>
              <div className="min-w-0">
                <h2 className="truncate text-xl font-semibold">
                  {profile.username}
                </h2>
                <p className="text-sm text-muted-foreground">
                  Joined {profile.joinedAt}
                </p>
                <p className="mt-1 text-sm">{profile.bio}</p>
              </div>
            </div>

            <Separator />

            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              {profile.stats.map(stat => (
                <div key={stat.label}>
                  <p className="text-2xl font-semibold tabular-nums">
                    {stat.value}
                  </p>
                  <p className="text-sm text-muted-foreground">{stat.label}</p>
                  {stat.hint && (
                    <p className="text-xs text-muted-foreground">{stat.hint}</p>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="flex flex-col gap-3">
            <h2 className="font-semibold">Most played</h2>
            <div className="flex items-center gap-3">
              <NationAvatar nation={profile.favouriteNation} className="size-10" />
              <div>
                <p className="font-medium">{profile.favouriteNation}</p>
                <p className="text-sm text-muted-foreground">
                  17 of 48 games
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="flex flex-col gap-3">
            <h2 className="font-semibold">Recent results</h2>
            <div className="flex flex-col gap-3">
              {profile.recentResults.map(result => (
                <div
                  key={result.gameName}
                  className="flex items-center gap-3"
                >
                  <NationAvatar nation={result.nation} />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">
                      {result.gameName}
                    </p>
                    <p className="truncate text-sm text-muted-foreground">
                      {result.nation} · {result.finishedAt}
                    </p>
                  </div>
                  <Badge variant={outcomeVariant[result.outcome]}>
                    {result.outcome}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </ScreenContainer>
    </HomeShell>
  );
};

export { PlayerProfile };
