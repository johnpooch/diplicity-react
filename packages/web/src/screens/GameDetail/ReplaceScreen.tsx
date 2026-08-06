import React, { Suspense } from "react";
import { useNavigate } from "react-router";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import { Clock, Loader2, MessageSquare, MessageSquareOff, Star, UserX } from "lucide-react";

import { GameDetailAppBar } from "./AppBar";
import { Panel } from "@/components/Panel";
import { Notice } from "@/components/Notice";
import { RemainingTimeDisplay } from "@/components/RemainingTimeDisplay";
import {
  NationFlag,
  findNationColor,
  findNationFlagUrl,
} from "@/components/NationFlag";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  ScreenCard,
  ScreenCardContent,
  ScreenCardHeader,
} from "@/components/ui/screen-card";
import { CardTitle } from "@/components/ui/card";
import {
  useGameMembersReplaceCreate,
  useGamePhaseRetrieve,
  useGameRetrieveSuspense,
  getGameRetrieveQueryKey,
  getGamesListQueryKey,
} from "@/api/generated/endpoints";
import { useGameVariant } from "@/hooks/useGameVariant";
import { useRequiredParams } from "@/hooks";
import { useIsMobile } from "@/hooks/use-mobile";
import { getCurrentPhaseId, getGameLandingPath } from "@/util";

interface DetailRowProps {
  icon: React.ReactNode;
  label: string;
  value: React.ReactNode;
}

const DetailRow: React.FC<DetailRowProps> = ({ icon, label, value }) => (
  <div className="flex items-center justify-between py-3 px-2">
    <div className="flex items-center gap-3">
      <div className="text-muted-foreground">{icon}</div>
      <span className="text-sm">{label}</span>
    </div>
    <div className="text-sm text-muted-foreground">{value}</div>
  </div>
);

const ReplaceContent: React.FC = () => {
  const { gameId, memberId } = useRequiredParams<{
    gameId: string;
    memberId: string;
  }>();
  const navigate = useNavigate();
  const isMobile = useIsMobile();
  const queryClient = useQueryClient();
  const replaceMutation = useGameMembersReplaceCreate();

  const { data: game } = useGameRetrieveSuspense(gameId);
  const variant = useGameVariant(game);

  const currentPhaseId = getCurrentPhaseId(game);
  const { data: currentPhase } = useGamePhaseRetrieve(
    gameId,
    currentPhaseId ?? 0,
    { query: { enabled: !!currentPhaseId } }
  );

  const member = game.members.find(m => m.id === Number(memberId));

  if (game.status !== "active") {
    return (
      <Notice
        icon={UserX}
        title="Game not in progress"
        message="This seat can only be taken over while the game is running."
      />
    );
  }

  if (game.members.some(m => m.isCurrentUser)) {
    return (
      <Notice
        icon={UserX}
        title="Already playing"
        message="You are already playing in this game."
      />
    );
  }

  if (!member?.replaceable) {
    return (
      <Notice
        icon={UserX}
        title="Seat unavailable"
        message="This seat is not open for replacement."
      />
    );
  }

  const nation = member.nation ?? "This nation";
  const supplyCenterCount = currentPhase?.supplyCenters.filter(
    sc => sc.nation.name === member.nation
  ).length;
  const reason = member.kicked
    ? `Removed from the game by ${game.gameMaster ? "the Game Master" : "the game creator"}.`
    : "Stopped submitting orders and fell into civil disorder.";

  const handleTakeOver = async () => {
    try {
      await replaceMutation.mutateAsync({ gameId, memberId: Number(memberId) });
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: getGameRetrieveQueryKey(gameId),
        }),
        queryClient.invalidateQueries({ queryKey: getGamesListQueryKey() }),
      ]);
      toast.success(`You are now playing ${nation}`);
      navigate(getGameLandingPath(game, isMobile));
    } catch {
      toast.error("Failed to take over the seat");
    }
  };

  return (
    <ScreenCard>
      <ScreenCardHeader>
        <div className="flex items-center gap-3">
          {member.nation && variant && (
            <NationFlag
              flagUrl={findNationFlagUrl(variant.nations, member.nation)}
              alt={member.nation}
              size="lg"
              className="size-8"
              color={findNationColor(variant.nations, member.nation)}
            />
          )}
          <CardTitle>{nation}</CardTitle>
        </div>
      </ScreenCardHeader>
      <ScreenCardContent className="divide-y">
        <p className="text-sm text-muted-foreground px-2 pb-3">{reason}</p>

        <DetailRow
          icon={<Star className="size-4" />}
          label="Supply centres"
          value={
            supplyCenterCount !== undefined ? (
              supplyCenterCount
            ) : (
              <Skeleton className="h-3 w-4" />
            )
          }
        />
        <DetailRow
          icon={<Clock className="size-4" />}
          label={currentPhase ? currentPhase.name : "Current phase"}
          value={
            currentPhase ? (
              <RemainingTimeDisplay
                remainingTime={currentPhase.remainingTime}
                scheduledResolution={currentPhase.scheduledResolution}
                isPaused={game.isPaused}
              />
            ) : (
              <Skeleton className="h-3 w-16" />
            )
          }
        />
        <DetailRow
          icon={
            game.pressType === "no_press" ? (
              <MessageSquareOff className="size-4" />
            ) : (
              <MessageSquare className="size-4" />
            )
          }
          label="Press"
          value={game.pressType === "no_press" ? "No Press" : "Full Press"}
        />

        <div className="pt-4">
          <Button
            className="w-full"
            disabled={replaceMutation.isPending}
            onClick={handleTakeOver}
          >
            {replaceMutation.isPending && (
              <Loader2 className="size-4 animate-spin" />
            )}
            Take Over {nation}
          </Button>
        </div>
      </ScreenCardContent>
    </ScreenCard>
  );
};

const ReplaceScreenSkeleton: React.FC = () => (
  <ScreenCard>
    <ScreenCardHeader>
      <Skeleton className="h-6 w-32" />
    </ScreenCardHeader>
    <ScreenCardContent className="divide-y">
      <Skeleton className="h-4 w-64 mb-3" />
      <Skeleton className="h-12 w-full" />
      <Skeleton className="h-12 w-full" />
      <Skeleton className="h-12 w-full" />
      <div className="pt-4">
        <Skeleton className="h-9 w-full" />
      </div>
    </ScreenCardContent>
  </ScreenCard>
);

const ReplaceScreen: React.FC = () => {
  const navigate = useNavigate();
  const { gameId, phaseId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
  }>();

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <GameDetailAppBar
        title="Replace Player"
        onNavigateBack={() => navigate(`/game/${gameId}/phase/${phaseId}`)}
        variant="secondary"
      />
      <div className="flex-1 overflow-y-auto">
        <Panel>
          <Panel.Content>
            <Suspense fallback={<ReplaceScreenSkeleton />}>
              <ReplaceContent />
            </Suspense>
          </Panel.Content>
        </Panel>
      </div>
    </div>
  );
};

export { ReplaceScreen };
