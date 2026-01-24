import React from "react";
import { Calendar, Users, Lock, Unlock, User, Map } from "lucide-react";

import { Skeleton } from "@/components/ui/skeleton";
import { GameStatusAlerts } from "@/components/GameStatusAlerts";
import {
  useGameRetrieveSuspense,
  useGamePhaseRetrieve,
  useVariantsListSuspense,
} from "@/api/generated/endpoints";
import { getCurrentPhaseId } from "@/util";
import { InteractiveMap } from "@/components/InteractiveMap/InteractiveMap";
import { MemberAvatarGroup } from "@/components/MemberAvatarGroup";
import { CardTitle } from "@/components/ui/card";
import {
  ScreenCard,
  ScreenCardContent,
  ScreenCardHeader,
} from "@/components/ui/screen-card";
import { useRequiredParams } from "@/hooks";

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

interface GameInfoContentProps {
  onNavigateToPlayerInfo: () => void;
}

export const GameInfoContent: React.FC<GameInfoContentProps> = ({
  onNavigateToPlayerInfo,
}) => {
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

  return (
    <>
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
                  onClick={onNavigateToPlayerInfo}
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
    </>
  );
};
