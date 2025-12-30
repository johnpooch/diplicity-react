import React, { Suspense } from "react";
import { useParams, useNavigate } from "react-router";
import {
  Calendar,
  Users,
  Lock,
  Unlock,
  User,
  Map,
  UserPlus,
  UserMinus,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { GameDropdownMenu } from "@/components/GameDropdownMenu";
import { GameStatusAlerts } from "@/components/GameStatusAlerts";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  useGameRetrieveSuspense,
  useGamePhaseRetrieveSuspense,
  useVariantsListSuspense,
  useGameJoinCreate,
  useGameLeaveDestroy,
} from "@/api/generated/endpoints";
import { getCurrentPhaseId } from "@/util";
import { InteractiveMap } from "@/components/InteractiveMap/InteractiveMap";
import { MemberAvatarGroup } from "@/components/MemberAvatarGroup.new";
import { CardTitle } from "../../components/ui/card";
import {
  ScreenCard,
  ScreenCardContent,
  ScreenCardHeader,
} from "../../components/ui/screen-card";
import { ScreenHeader } from "../../components/ui/screen-header";
import { ScreenContainer } from "../../components/ui/screen-container";

interface MetadataRowProps {
  icon: React.ReactNode;
  label: string;
  value: React.ReactNode;
}

const MetadataRow: React.FC<MetadataRowProps> = ({ icon, label, value }) => {
  return (
    <div className="flex items-center justify-between py-3 px-2">
      <div className="flex items-center gap-3">
        <div className="text-muted-foreground">{icon}</div>
        <span className="text-sm">{label}</span>
      </div>
      <div className="text-sm text-muted-foreground">{value}</div>
    </div>
  );
};

const GameInfo: React.FC = () => {
  const { gameId } = useParams<{ gameId: string }>();
  if (!gameId) throw new Error("gameId is required");

  const navigate = useNavigate();
  const { data: game } = useGameRetrieveSuspense(gameId);
  const { data: variants } = useVariantsListSuspense();
  const joinGameMutation = useGameJoinCreate();
  const leaveGameMutation = useGameLeaveDestroy();

  const currentPhaseId = getCurrentPhaseId(game);
  const { data: currentPhase } = useGamePhaseRetrieveSuspense(
    gameId,
    currentPhaseId ?? 0,
    { query: { enabled: !!currentPhaseId } }
  );

  const variant = variants.find(v => v.id === game.variantId);

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
        title="Game Info"
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
        <ScreenCardHeader>
          <CardTitle>{game.name}</CardTitle>
        </ScreenCardHeader>
        <ScreenCardContent>
          <MetadataRow
            icon={<Map className="size-4" />}
            label="Variant"
            value={variant?.name ?? <Skeleton className="h-4 w-24" />}
          />
          <MetadataRow
            icon={<Calendar className="size-4" />}
            label="Phase deadlines"
            value={
              game.movementPhaseDuration ?? <Skeleton className="h-4 w-24" />
            }
          />
          <MetadataRow
            icon={
              game.private ? (
                <Lock className="size-4" />
              ) : (
                <Unlock className="size-4" />
              )
            }
            label="Visibility"
            value={game.private ? "Private" : "Public"}
          />
          <MetadataRow
            icon={<Users className="size-4" />}
            label="Players"
            value={
              variant ? (
                <MemberAvatarGroup
                  members={game.members}
                  variant={variant.id}
                  victory={game.victory ?? undefined}
                  onClick={handlePlayerInfo}
                />
              ) : (
                <Skeleton className="h-8 w-24" />
              )
            }
          />
          <MetadataRow
            icon={<Users className="size-4" />}
            label="Number of nations"
            value={
              variant?.nations.length.toString() ?? (
                <Skeleton className="h-4 w-8" />
              )
            }
          />
          <MetadataRow
            icon={<Calendar className="size-4" />}
            label="Start year"
            value={
              variant?.templatePhase.year?.toString() ?? (
                <Skeleton className="h-4 w-12" />
              )
            }
          />
          <MetadataRow
            icon={<User className="size-4" />}
            label="Original author"
            value={variant?.author ?? <Skeleton className="h-4 w-24" />}
          />
          {variant && currentPhase ? (
            <div className="w-full aspect-square overflow-hidden">
              <InteractiveMap
                variant={variant}
                phase={currentPhase}
                orders={[]}
                selected={[]}
                interactive={false}
                style={{ width: "100%", height: "100%" }}
              />
            </div>
          ) : (
            <Skeleton className="w-full aspect-square rounded-lg" />
          )}
        </ScreenCardContent>
      </ScreenCard>
    </ScreenContainer>
  );
};

const GameInfoSuspense: React.FC = () => {
  return (
    <div className="w-full space-y-4">
      <Suspense fallback={<div></div>}>
        <GameInfo />
      </Suspense>
    </div>
  );
};

export { GameInfoSuspense as GameInfo };
