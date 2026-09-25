import React, { Suspense } from "react";
import { useNavigate } from "react-router";
import { GameDetailAppBar } from "./AppBar";
import { Panel } from "@/components/Panel";
import {
  PlayerProfileContent,
  PlayerProfileContentSkeleton,
} from "@/components/PlayerProfileContent";
import { useRequiredParams } from "@/hooks";

const PlayerProfileScreen: React.FC = () => {
  const navigate = useNavigate();
  const { gameId, phaseId, userId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
    userId: string;
  }>();

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <GameDetailAppBar
        title="Player Profile"
        onNavigateBack={() =>
          navigate(`/game/${gameId}/phase/${phaseId}/player-info`)
        }
        variant="secondary"
      />
      <div className="flex-1 overflow-y-auto">
        <Panel>
          <Panel.Content className="px-3 py-4">
            <Suspense fallback={<PlayerProfileContentSkeleton />}>
              <PlayerProfileContent userId={Number(userId)} />
            </Suspense>
          </Panel.Content>
        </Panel>
      </div>
    </div>
  );
};

export { PlayerProfileScreen };
