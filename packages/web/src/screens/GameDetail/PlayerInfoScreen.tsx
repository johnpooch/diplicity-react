import React, { Suspense } from "react";
import { GameDetailAppBar } from "./AppBar";
import { Panel } from "@/components/Panel";
import { PlayerInfoContent } from "@/components/PlayerInfoContent";

const PlayerInfoScreen: React.FC = () => {
  return (
    <div className="flex flex-col flex-1 min-h-0">
      <GameDetailAppBar title="Player Info" />
      <div className="flex-1 overflow-y-auto">
        <Panel>
          <Panel.Content className="px-4">
            <PlayerInfoContent />
          </Panel.Content>
        </Panel>
      </div>
    </div>
  );
};

const PlayerInfoScreenSuspense: React.FC = () => (
  <Suspense fallback={<div></div>}>
    <PlayerInfoScreen />
  </Suspense>
);

export { PlayerInfoScreenSuspense as PlayerInfoScreen };
