import React, { Suspense } from "react";
import { Handshake } from "lucide-react";
import { Link, useNavigate } from "react-router";

import {
  useGameRetrieveSuspense,
  useGamesDrawProposalsList,
} from "@/api/generated/endpoints";
import {
  DrawProposalNotificationBadge,
  getDrawProposalNotificationCount,
} from "@/components/DrawProposalNotificationBadge";
import { GameDropdownMenu } from "@/components/GameDropdownMenu";
import { Panel } from "@/components/Panel";
import { PlayerInfoContent } from "@/components/PlayerInfoContent";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Button } from "@/components/ui/button";
import { useRequiredParams } from "@/hooks";
import { GameDetailAppBar } from "./AppBar";

const OverviewScreen: React.FC = () => {
  const navigate = useNavigate();
  const { gameId, phaseId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
  }>();
  const { data: game } = useGameRetrieveSuspense(gameId);

  const isStartedGame =
    game.status === "active" ||
    game.status === "completed" ||
    game.status === "abandoned";
  const showDrawProposals = !game.sandbox && isStartedGame;
  const { data: drawProposals } = useGamesDrawProposalsList(gameId, {
    query: { enabled: showDrawProposals },
  });
  const drawProposalNotificationCount =
    getDrawProposalNotificationCount(drawProposals);

  return (
    <div className="flex flex-1 min-h-0 flex-col">
      <GameDetailAppBar
        title="Overview"
        rightButton={
          <GameDropdownMenu
            game={game}
            onNavigateToGameInfo={() =>
              navigate(`/game/${gameId}/phase/${phaseId}/game-info`)
            }
          />
        }
      />
      <div className="flex-1 overflow-y-auto">
        <Panel>
          <Panel.Content>
            <PlayerInfoContent />
          </Panel.Content>
          {showDrawProposals && (
            <Panel.Footer divider>
              <Button asChild variant="outline" className="relative">
                <Link to={`/game/${gameId}/phase/${phaseId}/draw-proposals`}>
                  <Handshake className="size-4" />
                  Draw proposals
                  <DrawProposalNotificationBadge
                    count={drawProposalNotificationCount}
                  />
                </Link>
              </Button>
            </Panel.Footer>
          )}
        </Panel>
      </div>
    </div>
  );
};

const OverviewScreenSuspense: React.FC = () => (
  <QueryErrorBoundary>
    <Suspense fallback={<div />}>
      <OverviewScreen />
    </Suspense>
  </QueryErrorBoundary>
);

export { OverviewScreenSuspense as OverviewScreen };
