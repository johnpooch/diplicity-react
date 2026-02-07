import React from "react";
import { Calendar, Users, Lock, Unlock, User, Map, Trophy, Pause, Shield } from "lucide-react";

import { Skeleton } from "@/components/ui/skeleton";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { GameStatusAlerts } from "@/components/GameStatusAlerts";
import { DeadlineSummary } from "@/components/DeadlineSummary";
import {
  useGameRetrieveSuspense,
  useGamePhaseRetrieve,
  useVariantsListSuspense,
} from "@/api/generated/endpoints";
import { getCurrentPhaseId, formatDateTime } from "@/util";
import { InteractiveMap } from "@/components/InteractiveMap/InteractiveMap";
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
              <DeadlineSummary game={game} />
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
          {game.status === "completed" && game.victory && (
            <MetadataRow
              icon={<Trophy className="size-4" />}
              label={game.victory.type === "solo" ? "Winner" : "Draw"}
              value={game.victory.members.map(m => m.name).join(", ")}
            />
          )}
          {game.isPaused && game.pausedAt && (
            <MetadataRow
              icon={<Pause className="size-4" />}
              label="Paused since"
              value={formatDateTime(game.pausedAt)}
            />
          )}
          {game.nmrExtensionsAllowed > 0 && (
            <MetadataRow
              icon={<Shield className="size-4" />}
              label="NMR extensions"
              value={`${game.nmrExtensionsAllowed} per player`}
            />
          )}
          <MetadataRow
            icon={<Users className="size-4" />}
            label="Players"
            value={
              variant ? (
                <button
                  onClick={onNavigateToPlayerInfo}
                  className="flex -space-x-2"
                >
                  {game.members.slice(0, 7).map(member => (
                    <Avatar
                      key={member.id}
                      className="h-8 w-8 border-2 border-background"
                    >
                      <AvatarImage src={member.picture ?? undefined} />
                      <AvatarFallback>
                        {member.name?.[0]?.toUpperCase() ?? "?"}
                      </AvatarFallback>
                    </Avatar>
                  ))}
                  {game.members.length > 7 && (
                    <div className="h-8 w-8 rounded-full bg-muted border-2 border-background flex items-center justify-center text-xs">
                      +{game.members.length - 7}
                    </div>
                  )}
                </button>
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
