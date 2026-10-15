import React from "react";
import {
  Calendar,
  ChevronRight,
  Lock,
  MessageCircleOff,
  Pause,
  ShieldPlus,
  Trophy,
} from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { GameStatusAlerts } from "@/components/GameStatusAlerts";
import { describePhaseTiming } from "@/components/DeadlineSummary";
import { MapView } from "@/components/MapView";
import { SettingsTable, type SettingsRow } from "@/components/SettingsTable";
import { buildVariantInfoRows } from "@/components/variantInfoRows";
import { useGameRetrieveSuspense } from "@/api/generated/endpoints";
import { useGameVariant } from "@/hooks/useGameVariant";
import { formatDateTime, formatTimeAgo } from "@/util";
import { useRequiredParams } from "@/hooks";

interface GameInfoContentProps {
  pendingAction?: React.ReactNode;
  onOpenVariantDetails?: () => void;
  showTitle?: boolean;
}

export const GameInfoContent: React.FC<GameInfoContentProps> = ({
  pendingAction,
  onOpenVariantDetails,
  showTitle = true,
}) => {
  const { gameId } = useRequiredParams<{ gameId: string }>();

  const { data: game } = useGameRetrieveSuspense(gameId);
  const variant = useGameVariant(game);

  const phaseDeadlineRows: SettingsRow[] = [
    {
      key: "movement",
      label: "Movement",
      value: describePhaseTiming(game, "movement"),
    },
    {
      key: "retreat",
      label: "Retreat/Adjustment",
      value: describePhaseTiming(game, "retreat"),
    },
    ...(game.nmrExtensionsAllowed > 0
      ? [
          {
            key: "extensions",
            label: "Deadline extensions",
            value: `${game.nmrExtensionsAllowed} per player`,
            info: "If a player does not submit orders on time, a deadline extension is used.",
          },
        ]
      : []),
  ];

  const settingsRows: SettingsRow[] = [
    {
      key: "created",
      icon: Calendar,
      label: "Created",
      value: formatTimeAgo(game.createdAt),
    },
    ...(game.private
      ? [{ key: "private", icon: Lock, label: "Private" }]
      : []),
    ...(game.pressType === "no_press"
      ? [
          {
            key: "gunboat",
            icon: MessageCircleOff,
            label: "Gunboat",
            info: "Player names are hidden and chat is disabled.",
          },
        ]
      : []),
    ...(game.commitmentRequirement === "committed"
      ? [
          {
            key: "commitment",
            icon: ShieldPlus,
            label: "High commitment players",
          },
        ]
      : []),
    ...(game.isPaused && game.pausedAt
      ? [
          {
            key: "paused",
            icon: Pause,
            label: "Paused since",
            value: formatDateTime(game.pausedAt),
          },
        ]
      : []),
    ...(game.status === "completed" && game.victory
      ? [
          {
            key: "victory",
            icon: Trophy,
            label: game.victory.type === "solo" ? "Winner" : "Draw",
            value: game.victory.members.map(m => m.name).join(", "),
          },
        ]
      : []),
  ];

  const variantDialogRows: SettingsRow[] = variant
    ? buildVariantInfoRows(variant)
    : [];

  const variantSummary = variant && (
    <div className="flex min-w-0 flex-1 flex-col gap-1">
      <h3 className="truncate font-semibold">{variant.name}</h3>
      {variant.description && (
        <p className="truncate text-sm text-muted-foreground">
          {variant.description}
        </p>
      )}
      {variant.rules && (
        <p className="flex items-center gap-1.5 text-sm text-muted-foreground">
          <Trophy className="size-4 shrink-0" />
          <span className="truncate">{variant.rules}</span>
        </p>
      )}
    </div>
  );

  return (
    <>
      <GameStatusAlerts game={game} variant={variant} action={pendingAction} />
      {showTitle && (
        <h1 className="truncate text-xl font-semibold leading-9">
          {game.name}
        </h1>
      )}
      <section className="flex flex-col gap-2">
        <h2 className="text-sm font-medium text-muted-foreground">Variant</h2>
        {variant ? (
          <Card className="overflow-hidden py-0">
            <CardContent className="flex flex-row p-0">
              <div className="w-1/3 shrink-0 overflow-hidden">
                <MapView
                  mode="static"
                  variant={variant}
                  phase={variant.templatePhase}
                  cover
                  className="aspect-video h-full w-full"
                />
              </div>
              {onOpenVariantDetails ? (
                <button
                  type="button"
                  onClick={onOpenVariantDetails}
                  className="flex min-w-0 flex-1 items-center gap-3 p-4 text-left"
                >
                  {variantSummary}
                  <ChevronRight className="size-4 shrink-0 text-muted-foreground" />
                </button>
              ) : (
                <Dialog>
                  <DialogTrigger asChild>
                    <button
                      type="button"
                      className="flex min-w-0 flex-1 items-center gap-3 p-4 text-left"
                    >
                      {variantSummary}
                      <ChevronRight className="size-4 shrink-0 text-muted-foreground" />
                    </button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>{variant.name}</DialogTitle>
                    </DialogHeader>
                    <div className="max-h-[60vh] overflow-y-auto">
                      <SettingsTable rows={variantDialogRows} />
                    </div>
                  </DialogContent>
                </Dialog>
              )}
            </CardContent>
          </Card>
        ) : (
          <Skeleton className="h-28 w-full rounded-xl" />
        )}
      </section>
      <section className="flex flex-col gap-2">
        <h2 className="text-sm font-medium text-muted-foreground">
          Phase deadlines
        </h2>
        <SettingsTable rows={phaseDeadlineRows} />
      </section>
      <section className="flex flex-col gap-2">
        <h2 className="text-sm font-medium text-muted-foreground">
          Game settings
        </h2>
        <SettingsTable rows={settingsRows} />
      </section>
    </>
  );
};
