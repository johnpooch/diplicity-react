import React, { Suspense } from "react";
import { useNavigate } from "react-router";
import { GameDetailAppBar } from "./AppBar";
import { Panel } from "@/components/Panel";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ScreenCard, ScreenCardContent } from "@/components/ui/screen-card";
import { useUsersRetrieveSuspense } from "@/api/generated/endpoints";
import { useRequiredParams } from "@/hooks";

const formatJoinDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString("en-US", { month: "long", year: "numeric" });
};

const UserProfile: React.FC = () => {
  const { userId } = useRequiredParams<{ userId: string }>();
  const { data: profile } = useUsersRetrieveSuspense(Number(userId));

  return (
    <ScreenCard>
      <ScreenCardContent className="space-y-4">
        <h2 className="text-lg font-semibold">Player Profile</h2>
        <div className="flex items-center gap-4">
          <Avatar className="size-12">
            <AvatarImage src={profile.picture ?? undefined} />
            <AvatarFallback>
              {profile.name?.[0]?.toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <div className="flex-1">
            <span className="text-lg font-medium">{profile.name}</span>
            <p className="text-sm text-muted-foreground">
              Joined {formatJoinDate(profile.createdAt)}
            </p>
          </div>
        </div>
      </ScreenCardContent>
    </ScreenCard>
  );
};

const UserProfileScreen: React.FC = () => {
  const navigate = useNavigate();
  const { gameId, phaseId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
  }>();

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <GameDetailAppBar
        title="Player Profile"
        onNavigateBack={() =>
          navigate(`/game/${gameId}/phase/${phaseId}/player-info`)
        }
        variant="secondary"
      />
      <div className="flex-1 overflow-y-auto">
        <Panel>
          <Panel.Content>
            <QueryErrorBoundary>
              <Suspense fallback={<div></div>}>
                <UserProfile />
              </Suspense>
            </QueryErrorBoundary>
          </Panel.Content>
        </Panel>
      </div>
    </div>
  );
};

const UserProfileScreenSuspense: React.FC = () => (
  <Suspense fallback={<div></div>}>
    <UserProfileScreen />
  </Suspense>
);

export { UserProfileScreenSuspense as UserProfileScreen };
