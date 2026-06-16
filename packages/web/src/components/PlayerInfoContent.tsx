import React from "react";
import { Shield, Star, Trophy, HardHat, Gavel } from "lucide-react";
import { Link, useParams } from "react-router";

import { CivilDisorderBadge } from "@/components/CivilDisorderBadge";
import { GameStatusAlerts } from "@/components/GameStatusAlerts";
import { NationFlag, findNationFlagUrl, findNationColor } from "@/components/NationFlag";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { ScreenCard, ScreenCardContent } from "@/components/ui/screen-card";
import { Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip";
import {
  useGameRetrieveSuspense,
  useGamePhaseRetrieve,
  useGamePhaseStatesList,
  useGameOrdersList,
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
  const { data: currentOrders } = useGameOrdersList(gameId, currentPhaseId ?? 0, {
    query: { enabled: !!currentPhaseId && game.status === "active" },
  });

  const variant = variants.find(v => v.id === game.variantId);

  const getSupplyCenterCount = (member: Member) => {
    if (!currentPhase) return undefined;
    return currentPhase.supplyCenters.filter(
      sc => sc.nation.name === member.nation
    ).length;
  };

  const getUnitCount = (member: Member) => {
    if (!currentPhase) return undefined;
    return currentPhase.units.filter(u => u.nation.name === member.nation).length;
  };

  const getRemainingOrders = (member: Member) => {
    if (!phaseStates || !currentOrders || !member.nation) return undefined;
    const ps = phaseStates.find(p => p.member.nation === member.nation);
    if (!ps) return undefined;
    const placed = currentOrders.filter(o => o.nation.name === member.nation).length;
    return ps.orderableProvinces.length - placed;
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
            const unitCount = getUnitCount(member);
            const remainingOrders = getRemainingOrders(member);
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
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <span className="inline-flex items-center gap-1">
                              <Star className="size-3" />
                              {supplyCenterCount !== undefined ? (
                                <span>{supplyCenterCount}</span>
                              ) : (
                                <Skeleton className="h-3 w-4" />
                              )}
                            </span>
                          </TooltipTrigger>
                          <TooltipContent>Supply centres</TooltipContent>
                        </Tooltip>
                        <span>•</span>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <span className="inline-flex items-center gap-1">
                              <HardHat className="size-3" />
                              {unitCount !== undefined ? (
                                <span>{unitCount}</span>
                              ) : (
                                <Skeleton className="h-3 w-4" />
                              )}
                            </span>
                          </TooltipTrigger>
                          <TooltipContent>Units</TooltipContent>
                        </Tooltip>
                        {game.status === "active" && (
                          <>
                            <span>•</span>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <span className="inline-flex items-center gap-1">
                                  <Gavel className="size-3" />
                                  {remainingOrders !== undefined ? (
                                    <span>{remainingOrders}</span>
                                  ) : (
                                    <Skeleton className="h-3 w-4" />
                                  )}
                                </span>
                              </TooltipTrigger>
                              <TooltipContent>Orders remaining</TooltipContent>
                            </Tooltip>
                          </>
                        )}
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
              </div>
            );
          })}
        </ScreenCardContent>
      </ScreenCard>
    </>
  );
};
