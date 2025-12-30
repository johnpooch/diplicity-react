import React, { Suspense } from "react";
import { useNavigate } from "react-router";

import { ScreenHeader } from "@/components/ui/screen-header";
import { ScreenContainer } from "@/components/ui/screen-container";
import { GameCard } from "@/components/GameCard.new";
import { Notice } from "@/components/Notice.new";
import { IconName } from "@/components/Icon";
import { Button } from "@/components/ui/button";
import {
  GameList,
  useGamesListSuspense,
  useVariantsListSuspense,
} from "@/api/generated/endpoints";

const SandboxGames: React.FC = () => {
  const navigate = useNavigate();

  const { data: games } = useGamesListSuspense({ sandbox: true, mine: true });
  const { data: variants } = useVariantsListSuspense();

  const getVariant = (game: GameList) => {
    const variant = variants.find(v => v.id === game.variantId);
    if (!variant) {
      throw new Error(`Variant not found for game ${game.id}`);
    }
    return variant;
  };

  const handleClickGame = (id: string) => {
    navigate(`/game/${id}`);
  };

  const handleClickGameInfo = (id: string) => {
    console.log("Game info clicked", id);
  };

  const handleClickPlayerInfo = (id: string) => {
    console.log("Player info clicked", id);
  };

  const handleClickJoinGame = (id: string) => {
    console.log("Join game clicked", id);
  };

  const handleClickCreateSandbox = () => {
    navigate("/create-game?sandbox=true");
  };

  return (
    <div className="space-y-4">
      {games && games.length > 0 ? (
        games.map(game => (
          <GameCard
            key={game.id}
            game={game}
            variant={getVariant(game)}
            phaseId={game.phases[0]}
            map={<div />}
            onClickGame={handleClickGame}
            onClickGameInfo={handleClickGameInfo}
            onClickPlayerInfo={handleClickPlayerInfo}
            onClickJoinGame={handleClickJoinGame}
          />
        ))
      ) : (
        <Notice
          title="No sandbox games found"
          message="Practice by controlling all nations. No time limits—resolve when ready."
          icon={IconName.Sandbox}
          actions={
            <Button onClick={handleClickCreateSandbox}>
              Create a sandbox game
            </Button>
          }
        />
      )}
    </div>
  );
};

const SandboxGamesSuspense: React.FC = () => {
  return (
    <ScreenContainer>
      <ScreenHeader title="Sandbox Games" />
      <Suspense fallback={<div></div>}>
        <SandboxGames />
      </Suspense>
    </ScreenContainer>
  );
};

export { SandboxGamesSuspense as SandboxGames };
