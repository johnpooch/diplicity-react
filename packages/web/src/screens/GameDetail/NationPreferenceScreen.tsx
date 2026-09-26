import React, { Suspense } from "react";
import { useNavigate } from "react-router";
import { GameDetailAppBar } from "./AppBar";
import { Panel } from "@/components/Panel";
import { NationPreferenceContent } from "@/components/NationPreferenceContent";
import { useRequiredParams } from "@/hooks";

const NationPreferenceScreen: React.FC = () => {
  const navigate = useNavigate();
  const { gameId } = useRequiredParams<{ gameId: string }>();

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <GameDetailAppBar
        title="Nation Preferences"
        onNavigateBack={() => navigate(`/game/${gameId}/game-info`)}
      />
      <div className="flex-1 overflow-y-auto">
        <Panel>
          <Panel.Content className="flex flex-col gap-4 px-3 py-4">
            <NationPreferenceContent />
          </Panel.Content>
        </Panel>
      </div>
    </div>
  );
};

const NationPreferenceScreenSuspense: React.FC = () => (
  <Suspense fallback={<div></div>}>
    <NationPreferenceScreen />
  </Suspense>
);

export { NationPreferenceScreenSuspense as NationPreferenceScreen };
