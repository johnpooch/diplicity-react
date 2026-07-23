import React, { useState } from "react";
import { Bot, Shield, Star, Trophy, UserPlus, X } from "lucide-react";
import { Link, useParams } from "react-router";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";

import { AddBotSheet } from "@/components/AddBotSheet";
import { CivilDisorderBadge } from "@/components/CivilDisorderBadge";
import { CommitmentBadge } from "@/components/CommitmentBadge";
import { GameStatusAlerts } from "@/components/GameStatusAlerts";
import { NationFlag, findNationFlagUrl, findNationColor } from "@/components/NationFlag";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { ScreenCard, ScreenCardContent } from "@/components/ui/screen-card";
import {
  useGameRetrieveSuspense,
  useGamePhaseRetrieve,
  useGameKickDestroy,
  useUserRetrieveSuspense,
  getGameAvailableBotsListQueryKey,
  getGameRetrieveQueryKey,
  Member,
} from "@/api/generated/endpoints";
import { useGameVariant } from "@/hooks/useGameVariant";
import { getCurrentPhaseId } from "@/util";
import { useRequiredParams } from "@/hooks";

export const PlayerInfoContent: React.FC = () => {
  const { gameId } = useRequiredParams<{ gameId: string }>();
  const { phaseId } = useParams<{ phaseId: string }>();

  const { data: game } = useGameRetrieveSuspense(gameId);
  const variant = useGameVariant(game);
  const { data: userProfile } = useUserRetrieveSuspense();
  const queryClient = useQueryClient();
  const kickMutation = useGameKickDestroy();

  const [addBotOpen, setAddBotOpen] = useState(false);

  const currentPhaseId = getCurrentPhaseId(game);
  const { data: currentPhase } = useGamePhaseRetrieve(
    gameId,
    currentPhaseId ?? 0,
    { query: { enabled: !!currentPhaseId } }
  );

  const getSupplyCenterCount = (member: Member) => {
    if (!currentPhase) return undefined;
    return currentPhase.supplyCenters.filter(
      sc => sc.nation.name === member.nation
    ).length;
  };

  const winnerIds = game.victory?.members?.map(m => m.id) || [];

  const isPending = game.status === "pending";
  const playableSeats = variant
    ? variant.nations.filter(n => !n.nonPlayable).length
    : 0;
  const openSeats = isPending
    ? Math.max(0, playableSeats - game.members.length)
    : 0;
  const canAddBots =
    isPending && game.canManage && userProfile.canCreateBotGames;

  const handleRemoveBot = async (member: Member) => {
    try {
      await kickMutation.mutateAsync({ gameId, memberId: member.id });
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: getGameRetrieveQueryKey(gameId),
        }),
        queryClient.invalidateQueries({
          queryKey: getGameAvailableBotsListQueryKey(gameId),
        }),
      ]);
      toast.success(`${member.name} removed from the game`);
    } catch {
      toast.error("Failed to remove AI player");
    }
  };

  return (
    <>
      <GameStatusAlerts game={game} variant={variant} />

      <ScreenCard>
        <ScreenCardContent className="divide-y">
          {game.gameMaster && (
            <div className="flex items-center gap-4 py-4 first:pt-0 last:pb-0">
              <Avatar className="size-8">
                <AvatarImage src={game.gameMaster.picture ?? undefined} />
                <AvatarFallback>
                  {game.gameMaster.name[0]?.toUpperCase() ?? "?"}
                </AvatarFallback>
              </Avatar>
              <div className="flex items-center gap-2 flex-wrap">
                <Link
                  to={`/player/${game.gameMaster.userId}`}
                  className="font-medium text-primary underline-offset-4 hover:underline"
                >
                  {game.gameMaster.name}
                </Link>
                <Badge variant="secondary" className="gap-1">
                  <Shield className="size-3" />
                  Game Master
                </Badge>
              </div>
            </div>
          )}
          {game.members.map(member => {
            const supplyCenterCount = getSupplyCenterCount(member);
            const isWinner = winnerIds.includes(member.id);

            return (
              <div
                key={member.id}
                className="flex items-center gap-4 py-4 first:pt-0 last:pb-0"
              >
                {member.nation && variant && (
                  <NationFlag
                    flagUrl={findNationFlagUrl(variant.nations, member.nation)}
                    alt={member.nation}
                    size="lg"
                    className="size-8"
                    color={findNationColor(variant.nations, member.nation)}
                  />
                )}

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    {member.userId ? (
                      <Link
                        to={
                          phaseId
                            ? `/game/${gameId}/phase/${phaseId}/player/${member.userId}`
                            : `/player/${member.userId}`
                        }
                        className="font-medium text-primary underline-offset-4 hover:underline"
                      >
                        {member.name}
                      </Link>
                    ) : (
                      <span className="font-medium">{member.name}</span>
                    )}
                    {member.isBot && (
                      <Badge variant="secondary" className="gap-1">
                        <Bot className="size-3" />
                        Bot
                      </Badge>
                    )}
                    {!member.isBot && member.commitment && (
                      <CommitmentBadge commitment={member.commitment} />
                    )}
                    {member.isGameCreator && (
                      <Badge variant="secondary" className="gap-1">
                        <Shield className="size-3" />
                        Game Creator
                      </Badge>
                    )}
                    {isWinner && (
                      <Badge variant="default" className="gap-1">
                        <Trophy className="size-3" />
                        {game.victory?.type === "solo" ? "Winner" : "Draw"}
                      </Badge>
                    )}
                    {member.civilDisorder && <CivilDisorderBadge />}
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
                        {game.nmrExtensionsAllowed > 0 && (
                          <>
                            <span>•</span>
                            <span>{member.nmrExtensionsRemaining} ext. remaining</span>
                          </>
                        )}
                      </span>
                    </div>
                  )}
                </div>

                {isPending && game.canManage && member.isBot && (
                  <Button
                    variant="ghost"
                    size="icon"
                    aria-label={`Remove ${member.name}`}
                    disabled={kickMutation.isPending}
                    onClick={() => handleRemoveBot(member)}
                  >
                    <X className="size-4" />
                  </Button>
                )}
              </div>
            );
          })}
          {Array.from({ length: openSeats }, (_, index) =>
            canAddBots ? (
              <button
                key={`open-seat-${index}`}
                onClick={() => setAddBotOpen(true)}
                className="flex items-center gap-4 py-4 first:pt-0 last:pb-0 w-full text-left"
              >
                <div className="size-8 rounded-full border border-dashed border-muted-foreground/50 flex items-center justify-center">
                  <UserPlus className="size-4 text-muted-foreground" />
                </div>
                <span className="font-medium text-primary underline-offset-4 hover:underline">
                  Add AI player
                </span>
              </button>
            ) : (
              <div
                key={`open-seat-${index}`}
                className="flex items-center gap-4 py-4 first:pt-0 last:pb-0"
              >
                <div className="size-8 rounded-full border border-dashed border-muted-foreground/50" />
                <span className="text-muted-foreground">Open seat</span>
              </div>
            )
          )}
        </ScreenCardContent>
      </ScreenCard>

      {canAddBots && (
        <AddBotSheet
          gameId={gameId}
          open={addBotOpen && openSeats > 0}
          onOpenChange={setAddBotOpen}
        />
      )}
    </>
  );
};
