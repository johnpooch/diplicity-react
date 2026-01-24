import React from "react";
import { Star, Trophy } from "lucide-react";

import { GameStatusAlerts } from "@/components/GameStatusAlerts";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
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
import { Flags } from "@/assets/flags";
import { useRequiredParams } from "@/hooks";

export const PlayerInfoContent: React.FC = () => {
  const { gameId } = useRequiredParams<{ gameId: string }>();

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
            const nationFlag =
              Flags[(variant?.id ?? "") as keyof typeof Flags]?.[
                member.nation?.toLowerCase() as keyof (typeof Flags)[keyof typeof Flags]
              ];

            const supplyCenterCount = getSupplyCenterCount(member);
            const isWinner = winnerIds.includes(member.id);

            return (
              <div
                key={member.id}
                className="flex items-center gap-4 py-4 first:pt-0 last:pb-0"
              >
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
    </>
  );
};
