import React, { Suspense } from "react";
import { useNavigate, useParams } from "react-router";
import {
  Star,
  UserPlus,
  UserMinus,
  Trophy,
} from "lucide-react";

import { GameStatusAlerts } from "@/components/GameStatusAlerts";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { ScreenCard, ScreenCardContent } from "@/components/ui/screen-card";
import { ScreenHeader } from "@/components/ui/screen-header";
import { ScreenContainer } from "@/components/ui/screen-container";
import { GameDropdownMenu } from "@/components/GameDropdownMenu";
import {
  useGameRetrieveSuspense,
  useGamePhaseRetrieve,
  useVariantsListSuspense,
  Member,
  useGameJoinCreate,
  useGameLeaveDestroy,
} from "@/api/generated/endpoints";
import { getCurrentPhaseId } from "@/util";
import { Flags } from "@/assets/flags";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "../../components/ui/tooltip";
import { Button } from "../../components/ui/button";

const PlayerInfo: React.FC = () => {
  const { gameId } = useParams<{ gameId: string }>();
  if (!gameId) throw new Error("gameId is required");

  const navigate = useNavigate();
  const { data: game } = useGameRetrieveSuspense(gameId);
  const { data: variants } = useVariantsListSuspense();
  const joinGameMutation = useGameJoinCreate();
  const leaveGameMutation = useGameLeaveDestroy();

  const currentPhaseId = getCurrentPhaseId(game);
  const { data: currentPhase } = useGamePhaseRetrieve(
    gameId,
    currentPhaseId ?? 0,
    { query: { enabled: !!currentPhaseId } }
  );

  const variant = variants.find(v => v.id === game.variantId);

  const getSupplyCenterCount = (member: Member) => {
    if (!currentPhase) return undefined;
    return currentPhase.supplyCenters.filter(
      sc => sc.nation.name === member.nation
    ).length;
  };

  const winnerIds = game.victory?.members?.map(m => m.id) || [];

  const handleJoinGame = async () => {
    await joinGameMutation.mutateAsync({ gameId, data: {} });
  };

  const handleLeaveGame = async () => {
    await leaveGameMutation.mutateAsync({ gameId });
  };

  const handlePlayerInfo = () => {
    navigate(`/player-info/${gameId}`);
  };

  const handleGameInfo = () => {
    navigate(`/game-info/${gameId}`);
  };

  const joinLeaveButton = game.canJoin ? (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          onClick={handleJoinGame}
          disabled={joinGameMutation.isPending}
          variant="outline"
          aria-label="Join game"
        >
          <UserPlus className="size-4" />
        </Button>
      </TooltipTrigger>
      <TooltipContent>
        <p>Join game</p>
      </TooltipContent>
    </Tooltip>
  ) : (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          onClick={handleLeaveGame}
          disabled={leaveGameMutation.isPending}
          variant="outline"
          aria-label="Leave game"
        >
          <UserMinus className="size-4" />
        </Button>
      </TooltipTrigger>
      <TooltipContent>
        <p>Leave game</p>
      </TooltipContent>
    </Tooltip>
  );

  return (
    <ScreenContainer>
      <ScreenHeader
        title="Player Info"
        actions={
          <>
            {joinLeaveButton}
            <GameDropdownMenu
              gameId={game.id}
              onNavigateToGameInfo={handleGameInfo}
              onNavigateToPlayerInfo={handlePlayerInfo}
            />
          </>
        }
      />

      <GameStatusAlerts game={game} variant={variant} />

      <ScreenCard>
        <ScreenCardContent className="divide-y">
          {game.members.map(member => {
            const nationFlag =
              Flags[(variant?.id ?? "") as keyof typeof Flags]?.[
                member.nation?.toLowerCase() as keyof (typeof Flags)[keyof typeof Flags]
              ];

            const supplyCenterCount = getSupplyCenterCount(member);
            const isWinner = winnerIds.includes(member.id);

            return (
              <div key={member.id} className="flex items-center gap-4 py-4 first:pt-0 last:pb-0">
                <div className="relative">
                  <Avatar className="size-12">
                    <AvatarImage src={member.picture ?? undefined} />
                    <AvatarFallback>
                      {member.nation?.toUpperCase()[0]}
                    </AvatarFallback>
                  </Avatar>
                  {member.nation && nationFlag && (
                    <span className="absolute -right-1 -bottom-1 inline-flex size-4 items-center justify-center rounded-full bg-white border-2 border-background">
                      <img
                        src={nationFlag}
                        alt={member.nation}
                        className="h-full w-full rounded-full object-cover"
                      />
                    </span>
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium">{member.name}</span>
                    {isWinner && (
                      <Badge variant="default" className="gap-1">
                        <Trophy className="size-3" />
                        {game.victory?.type === "solo" ? "Winner" : "Draw"}
                      </Badge>
                    )}
                  </div>

                  {member.nation && (
                    <div className="text-sm text-muted-foreground mt-1">
                      <span className="inline-flex items-center gap-2">
                        <span>{member.nation}</span>
                        <span>•</span>
                        <span className="inline-flex items-center gap-1">
                          <Star className="size-3" />
                          {supplyCenterCount !== undefined ? (
                            <span>{supplyCenterCount}</span>
                          ) : (
                            <Skeleton className="h-3 w-4" />
                          )}
                        </span>
                      </span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </ScreenCardContent>
      </ScreenCard>
    </ScreenContainer>
  );
};

const PlayerInfoSuspense: React.FC = () => {
  return (
    <div className="w-full">
      <Suspense fallback={<div></div>}>
        <PlayerInfo />
      </Suspense>
    </div>
  );
};

export { PlayerInfoSuspense as PlayerInfo };
