import React from "react";
import { Shield, Trophy } from "lucide-react";
import { Link, useParams } from "react-router";

import { CivilDisorderBadge } from "@/components/CivilDisorderBadge";
import { GameStatusAlerts } from "@/components/GameStatusAlerts";
import { PlayerCard } from "@/components/PlayerCard";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { ScreenCard, ScreenCardContent } from "@/components/ui/screen-card";
import {
  useGameRetrieveSuspense,
  useGamePhaseRetrieve,
  useGamePhaseStatesList,
  useVariantsListSuspense,
  Member,
} from "@/api/generated/endpoints";
import { getCurrentPhaseId } from "@/util";
import { useRequiredParams } from "@/hooks";

export const PlayerInfoContent: React.FC = () => {
  const { gameId } = useRequiredParams<{ gameId: string }>();
  const { phaseId } = useParams<{ phaseId: string }>();

  const { data: game } = useGameRetrieveSuspense(gameId);
  const { data: variants } = useVariantsListSuspense();

  const currentPhaseId = getCurrentPhaseId(game);
  const { data: currentPhase } = useGamePhaseRetrieve(
    gameId,
    currentPhaseId ?? 0,
    { query: { enabled: !!currentPhaseId } }
  );
  const { data: phaseStates } = useGamePhaseStatesList(gameId, {
    query: { enabled: !!currentPhaseId && game.status === "active" },
  });

  const variant = variants.find(v => v.id === game.variantId);

  const getSupplyCenterCount = (member: Member) => {
    if (!currentPhase) return undefined;
    return currentPhase.supplyCenters.filter(
      sc => sc.nation.name === member.nation
    ).length;
  };

  const winnerIds = game.victory?.members?.map(m => m.id) || [];

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
            const phaseState = phaseStates?.find(
              ps => ps.member.nation === member.nation
            );
            const unitCount = phaseState?.unitCount;
            const remainingOrders = phaseState?.remainingOrders;
            const isWinner = winnerIds.includes(member.id);

            return (
              <div
                key={member.id}
                className="py-4 first:pt-0 last:pb-0"
              >
                {variant ? (
                  <PlayerCard
                    member={member}
                    variant={variant}
                    gameId={gameId}
                    phaseId={phaseId}
                    supplyCenterCount={supplyCenterCount}
                    unitCount={unitCount}
                    remainingOrders={remainingOrders}
                    showOrdersCount={game.status === "active"}
                    nmrExtensionsAllowed={game.nmrExtensionsAllowed}
                    isWinner={isWinner}
                    victoryType={game.victory?.type}
                  />
                ) : (
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium">{member.name}</span>
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
                )}
              </div>
            );
          })}
        </ScreenCardContent>
      </ScreenCard>
    </>
  );
};
