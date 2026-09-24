import React, { Suspense } from "react";
import { useNavigate } from "react-router";
import { GameDetailAppBar } from "./AppBar";
import { Panel } from "@/components/Panel";
import { MapView } from "@/components/MapView";
import { SettingsTable } from "@/components/SettingsTable";
import { buildVariantInfoRows } from "@/components/variantInfoRows";
import { Skeleton } from "@/components/ui/skeleton";
import { useGameRetrieveSuspense } from "@/api/generated/endpoints";
import { useGameVariant } from "@/hooks/useGameVariant";
import { useRequiredParams } from "@/hooks";

const VariantDetailsScreen: React.FC = () => {
  const navigate = useNavigate();
  const { gameId, phaseId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
  }>();
  const { data: game } = useGameRetrieveSuspense(gameId);
  const variant = useGameVariant(game);

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <GameDetailAppBar
        title={variant?.name ?? "Variant"}
        onNavigateBack={() => navigate(`/game/${gameId}/phase/${phaseId}/game-info`)}
        variant="secondary"
      />
      <div className="flex-1 overflow-y-auto">
        <Panel>
          <Panel.Content className="flex flex-col gap-4 px-3 py-4">
            {variant ? (
              <>
                <div className="w-full shrink-0 overflow-hidden rounded-xl">
                  <MapView
                    mode="static"
                    variant={variant}
                    phase={variant.templatePhase}
                    cover
                    className="aspect-video w-full"
                  />
                </div>
                <SettingsTable rows={buildVariantInfoRows(variant)} />
              </>
            ) : (
              <>
                <Skeleton className="aspect-video w-full rounded-xl" />
                <Skeleton className="h-40 w-full rounded-xl" />
              </>
            )}
          </Panel.Content>
        </Panel>
      </div>
    </div>
  );
};

const VariantDetailsScreenSuspense: React.FC = () => (
  <Suspense fallback={<div></div>}>
    <VariantDetailsScreen />
  </Suspense>
);

export { VariantDetailsScreenSuspense as VariantDetailsScreen };
