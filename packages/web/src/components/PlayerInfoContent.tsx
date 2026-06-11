import React from "react";
import { Shield, Star, Trophy } from "lucide-react";
import { Link, useParams } from "react-router";

import { CivilDisorderBadge } from "@/components/CivilDisorderBadge";
import { GameStatusAlerts } from "@/components/GameStatusAlerts";
import { NationFlag, findNationFlagUrl, findNationColor } from "@/components/NationFlag";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { ScreenCard, ScreenCardContent } from "@/components/ui/screen-card";
import {
  useGameRetrieveSuspense,
  useGamePhaseRetrieve,
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
          {game.members.map(member => {
            const supplyCenterCount = getSupplyCenterCount(member);
            const isWinner = winnerIds.includes(member.id);

            return (
              <div
                key={member.id}
                className="flex items-center gap-4 py-4 first:pt-0 last:pb-0"
              >
                {member.nation && variant ? (
                  <NationFlag
                    flagUrl={findNationFlagUrl(variant.nations, member.nation)}
                    alt={member.nation}
                    size="lg"
                    className="size-8"
                    color={findNationColor(variant.nations, member.nation)}
                  />
                ) : member.isGameMaster ? (
                  <NationFlag
                    flagUrl={member.picture}
                    alt="Game Master"
                    size="lg"
                    className="size-8"
                    color="#808080"
                  />
                ) : null}

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
                    {member.isGameMaster && (
                      <Badge variant="secondary" className="gap-1">
                        <Shield className="size-3" />
                        Game Master
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
              </div>
            );
          })}
        </ScreenCardContent>
      </ScreenCard>
    </>
  );
};
